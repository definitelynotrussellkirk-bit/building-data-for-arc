# Working notes: 9dcb885757dc

## 2026-09-28 review: contact-graph curriculum repair

### Root cause

The imported generator claimed “varied Manhattan-2 touch degrees,” but sampled
large sparse canvases by rejection. In a pinned 300-draw census per difficulty,
241 easy, 228 medium, and 215 hard inputs had only isolated objects. Those
examples all reduce the target rule to “paint every object color 2.” The public
examples instead use compact 7–8 by 7–10 canvases, five or six components, and
include pair and degree-3 hub graphs. The old generator also made the canonical
palette size unreachable and did not expose a falsifiable semantic contract.

### Decisions implemented

- Replace random scatter with six exact contact-graph templates: isolated,
  pair, chain, hub3, hub4, and dense.
- Schedule five teaching profiles (pair through dense) so every five-example
  window covers degree branches 0 through 5. Keep isolated as a lawful exact
  override because it is present in the canonical data.
- Keep every draw inside the canonical mechanical envelope: heights 7–8,
  widths 7–10, and five or six distinctly colored components.
- Alternate singleton and mixed-component shapes. Mixed profiles preserve the
  contact graph while making nearby-cell count differ from neighboring-object
  count.
- Pin `RULE_HASH=25bd5db7ed17`; leave the selected canonical Racket authority
  unchanged because canonical parity and authority synchronization pass.
- Reject unknown overrides and make all five declared axes exactly observable.
- Declare executable rivals and witnesses for all-isolated, binary-touch,
  direct-contact, nearby-cell-count, and degree-capped shortcuts.
- Add deterministic mutation fixtures and an episode-level
  `lesson_identifiable` contract.

### Evidence

- Baseline battery: 6 green, 2 advisory, 4 failed (`lint`, `defect_lint`,
  `dist_gate`, `override`).
- Task tests: 11 passed, including canonical parity, all 192 exact
  boundary/profile/style combinations, degree 0–5 schedule coverage,
  deterministic replay, mutation rejection, and analyzer behavior.
- Final battery: all 12 stages green.
- Semantic gate: 600/600 strict draws, all four canonical inputs accepted,
  declared witnesses and rivals verified, and 12/12 sampled lessons
  identifiable.
- Contact-graph analyzer: 60/60 valid draws; each of five teaching profiles
  appears 12 times; singleton/mixed styles split 30/30; degree branches 0–5
  all appear; all four canonical inputs pass.

### Known limits

- Generation uses a finite library of graph topologies rather than arbitrary
  realizable contact graphs. Geometric transforms and color permutations still
  produce many grids, but graph-shape diversity is intentionally bounded.
- Mixed components are small domino-like extensions, not arbitrary polyominoes.
- Individual pair or chain examples do not by themselves refute every rival;
  identifiability is guaranteed at the five-example lesson level.
- Difficulty changes a fixed-point-free input color permutation while
  preserving graph semantics. It does not represent a monotonic increase in
  topological difficulty.

The task-local analyzer in `workspace/analyze_contact_graph_distribution.py`
should be rerun after any schedule, profile, or shape change.
## Current reviewer considerations

Source SHA-256: `c39797613c66963c883c3b862128a186df6d59893f59314206c361942a5d7f8c`.

# Design decisions: 9dcb885757dc

The imported task had no retained associated design notes, so “original
rationale” below is either directly visible in version 1.1.1 source or marked
unknown. Decisions were made against the selected Racket authority, all four
canonical inputs, the immutable before battery, and pinned generated censuses.

## D1. Use compact canonical-scale canvases

**Choice.** Ordinary grids are 7–8 rows by 7–10 columns.

**Original rationale.** Unknown. The old generator used band-dependent ranges
roughly 9–14 by 12–18, apparently to make rejection sampling easier.

**Alternatives considered.** Keep the large ranges; mix large and canonical
anchors; allow 7–18 as independent axes.

**Probe/evidence.** Every canonical input lies in 7–8 by 7–10. The baseline
profile floor was 0/60 and the seven-color canonical palette was unreachable.
The final canonical profile floor and distribution gate are green.

**Failure modes/limits.** This narrows geometric scale diversity. Expanding it
later should preserve a nonzero canonical-scale floor and re-run the
contact-graph analyzer.

## D2. Generate contact graphs by construction

**Choice.** Use six fixed realizable graph families—isolated, pair, chain,
hub3, hub4, and dense—then apply deterministic transforms and color choices.

**Original rationale.** The old source stated `position_bias =
varied_touch_degrees`, but the placement algorithm only enforced free space;
it never enforced degree diversity.

**Alternatives considered.** Tune rejection probabilities; rejection-sample
against a requested degree multiset; build an arbitrary small graph embedding
solver.

**Probe/evidence.** The old 300-draw censuses had 215–241 all-isolated examples
per band. The template approach gives exact graph fingerprints, 60/60 valid
analysis draws, and branch coverage 0–5.

**Failure modes/limits.** Topology diversity is bounded by six families. An
embedding solver could broaden it, but would add search failures and weaken
exact override guarantees without evidence that Qwen training benefits.

## D3. Schedule five profiles; keep isolated override-only

**Choice.** Normal lessons cycle through pair, chain, hub3, hub4, and dense.
`isolated` stays in the declared profile domain because it is a lawful
canonical case.

**Original rationale.** The old generator had no schedule and therefore often
sampled the isolated case accidentally.

**Alternatives considered.** Six-demo lessons including isolated; remove
isolated entirely; keep all six but randomly select five.

**Probe/evidence.** The worker semantic contract accepts at most five demos.
All non-isolated profiles already include at least one degree-0 object, so the
five scheduled profiles cover branches 0–5. Sliding-window tests pass for every
start residue checked.

**Failure modes/limits.** A normal episode does not show the pure all-isolated
scene, though exact overrides and canonical evaluation still cover it.

## D4. Use five or six distinctly colored components

**Choice.** `n_components` is an exact 5–6 axis; every component has a distinct
nonzero input color.

**Original rationale.** The old generator used 3–5 components and distinct
colors. Distinct colors help make object identity visible, but the lower counts
were not justified by canonical evidence.

**Alternatives considered.** Preserve 3–5; allow 3–8; reuse colors across
separate components.

**Probe/evidence.** Canonical inputs have five or six components. Six are
needed for a degree-5 vertex, and a background plus six object colors reaches
the canonical palette size seven. The final distribution and profile gates are
green.

**Failure modes/limits.** Same-colored disconnected objects are not taught.
That ambiguity is unnecessary for the selected authority and would complicate
component observability.

## D5. Alternate singleton and mixed component styles

**Choice.** Each graph profile has `singletons` and `mixed` realizations. Mixed
styles add cells to selected objects while preserving graph edges.

**Original rationale.** The old generator used one-cell or short horizontal
objects, but did not guarantee that shape variation exposed a semantic
alternative.

**Alternatives considered.** All singletons; arbitrary polyomino growth; a
separate shape-size axis for every object.

**Probe/evidence.** The `count_nearby_cells` rival differs from the authority on
declared mixed witnesses. The analyzer reports a 30/30 style split, and named
witness tests verify the rival is actually refuted.

**Failure modes/limits.** Mixed shapes are modest domino-like extensions, not a
comprehensive polyomino curriculum.

## D6. Preserve the authority’s exact degree-to-color mapping

**Choice.** Recolor each object by degree: 0→2, 1→3, 2→4, 3→5, 4→6, and 5+→7.

**Original rationale.** This is dictated by the selected Racket program and
canonical outputs.

**Alternatives considered.** None for production. Competing mappings exist
only as executable semantic rivals.

**Probe/evidence.** Python `rule_mirror` matches all four canonical outputs;
Racket rule smoke, lint, and authority execution parity are green. The dense
six-object profile exercises degree 5→7.

**Failure modes/limits.** With at most six objects, degrees above five are not
separately observed; they intentionally share the authority’s 5+ class.

## D7. Make difficulty live without changing the lesson

**Choice.** Easy, medium, and hard apply different fixed-point-free cyclic
permutations to input object colors while preserving dimensions, graph
profile, style, and output semantics.

**Original rationale.** The imported difficulty bands changed sizes and counts,
but mostly changed isolation probability rather than meaningful difficulty.

**Alternatives considered.** Delete difficulty; map bands to increasingly dense
graphs; use larger components or canvases by band.

**Probe/evidence.** A TDD regression first demonstrated identical outputs from
all bands. The final test verifies all three input grids differ while their
graph degree multiset and profile match. Strict defect lint no longer reports
dead bands.

**Failure modes/limits.** The bands are representational variants, not a proven
monotonic cognitive-difficulty ladder.

## D8. Make every declared axis exact and observable

**Choice.** Declare only five axes that can be recovered from the returned grid:
height, width, component count, graph profile, and component style. Reject
unknown keys.

**Original rationale.** The old source declared singleton metadata axes and
accepted `**overrides` without unknown-key validation.

**Alternatives considered.** Mark old axes diagnostic; retain aliases; declare
incompatibility combinations.

**Probe/evidence.** Baseline override checking produced 7,683 findings plus
22,980 legacy multi-axis rejections and accepted a typo key. The final matrix
passes every case, recovers every axis exactly, and rejects unknown keys.

**Failure modes/limits.** Adding an axis now requires a structural observer and
full matrix support rather than a metadata-only knob. This is intentional.

## D9. Enforce structure before semantics

**Choice.** `self_check` rejects malformed grids, wrong object counts, repeated
component colors, side-adjacent distinct objects, unknown graph signatures,
wrong styles, hidden transformation branches, and mismatched override metadata.

**Original rationale.** The old check covered only a subset of color and
component-count invariants; its declared degenerate textures could pass.

**Alternatives considered.** A permissive authority-only check plus a separate
teaching check; relying on the Racket rule to reject malformed inputs.

**Probe/evidence.** Mutation fixtures fail before the implementation repair and
pass afterward. Final selfcheck, strict defect lint, canonical profile, and
semantic stages are green.

**Failure modes/limits.** This teaching grammar is narrower than every grid on
which the Racket program could execute. That is deliberate: execution validity
alone is not training suitability.

## D10. Declare rivals at the lesson level

**Choice.** Provide executable rivals, witnesses, and a five-demo
`lesson_identifiable` check.

**Original rationale.** None existed. Generic diversity and rule smoke could
pass while the data taught a shortcut.

**Alternatives considered.** Rely only on branch histograms; reject any single
draw on which a rival also works; use model-based evaluation.

**Probe/evidence.** The final semantic gate verifies all named witness/rival
claims and 12/12 sampled lessons. Per-draw analysis still shows expected rival
survival (for example, a degree cap works on profiles lacking degree 5), which
is why the episode is the correct unit.

**Failure modes/limits.** The contract can only test rivals someone names.
Future reviews should add plausible shortcuts rather than treating the current
set as exhaustive.

## D11. Do not edit the Racket authority

**Choice.** Pin `RULE_HASH=25bd5db7ed17` and leave canonical/base selected rule
text unchanged.

**Original rationale.** The active authority already solved every canonical
pair.

**Alternatives considered.** Synchronize the archival divergent `raw_code`;
rewrite the rule for readability.

**Probe/evidence.** Canonical parity, Racket lint, rule smoke, and selected
source execution parity all pass. The archival divergence is explicitly
reported and does not affect selected execution.

**Failure modes/limits.** The archival `raw_code` remains textually divergent.
Changing it without a source-governance reason would add churn without training
value.

## D12. Add a task-linked distribution analyzer

**Choice.** Retain `workspace/analyze_contact_graph_distribution.py` and its
JSON report.

**Original rationale.** No task-linked diagnostic existed; generic uniqueness
made the old distribution look healthier than it was.

**Alternatives considered.** A one-off notebook; extending the global battery
inside this task; manual montage inspection only.

**Probe/evidence.** The tool is covered by a subprocess regression test and
exits nonzero for malformed draws, rejected canonical inputs, or missing degree
branches.

**Failure modes/limits.** It imports this generator’s declared semantic
contract and is not a universal ARC metric. That task linkage is its purpose.
