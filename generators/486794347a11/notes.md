# Working notes: 486794347a11

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## 2026-09-28 review

The inherited 4.0.0 generator passed all twelve standard battery stages, but a
25,600-grid no-count census found two undeclared perfect proxies:

1. `K=3` iff the markers contain an adjacent pair or span both edges; otherwise
   `K=2`.
2. `K=2` iff the top-row markers form two contiguous runs; otherwise `K=3`.

Both rules fit every sampled generated input while disagreeing with lawful
canonical-style layouts. The four-phase marker schedule, not the Racket rule or
body grammar, caused the correlation.

The accepted 4.2.0 change uses an eight-slot marker-layout schedule crossing
marker count with adjacency, run count, span, gap size, edge contact, and
rightmost position. It retains canonical `[0,2]` and `[0,2,4]` layouts as normal
defaults. Three geometry rivals and their counterexample witnesses are now part
of the semantic contract.

A first after attempt kept `EXAMPLES_NEEDED = 3`; the semantic gate found three
reproducible lessons at sample index 22 where `marker_span_gap_scale` fit every
demo but differed on the query. Four consecutive demonstrations always contain
its counterexample, so the final contract declares four examples.

Final census over 25,600 grids:

- no exact single-feature geometry proxy;
- named rival accuracy: 37.5% geometry, 50% component-count, 75% span/min-gap;
- held-out depth-2 tree: 96.875%, down from 100% before.

The remaining high multivariate tree score is not by itself a defect: joint gap
features can reconstruct whether there are one or two gaps, which is a lawful
re-encoding of the intended two-versus-three marker count. Future reviews should
require a legal counterexample before treating such a learned expression as a
spurious rival.
## Current reviewer considerations

Source SHA-256: `d99d3bb001158d0e30650fcec5f505835a69b9c1ad122657a5ca4cc44b2a4b48`.

# Decisions for generator 486794347a11

## Design objective

Preserve the canonical rule and valid-input grammar while removing accidental
marker-layout correlations that let a learner choose the scale without learning
to count the color-1 cells in row 0. Keep exact overrides, canonical layouts,
body variation, deterministic generation, and all existing battery contracts.

## Input choices

### Grid height and width

- **Inherited choice:** height `7..12`, width `8..14`, with a scheduled bias
  toward canonical dimensions.
- **Original rationale:** explicit in source: retain canonical profiles while
  broadening dimensions and keeping scaled output area below input area.
- **Alternatives considered:** change canvas distributions to disrupt marker
  features; rejected because marker placement, not canvas size, was the root
  cause and dimension changes would disturb unrelated coverage.
- **Decision:** unchanged.
- **Probe/failure mode:** existing profile, distribution, diversity, override,
  and area checks remain the guardrails.

### Marker count

- **Inherited choice:** exactly two or three color-1 cells; ordinary defaults
  alternate by sample index.
- **Original rationale:** matches the canonical scale factors and makes every
  short lesson contain both labels.
- **Alternatives considered:** add scale factors outside `{2,3}`; rejected as a
  rule-domain expansion not justified by canonical evidence.
- **Decision:** unchanged.
- **Failure mode:** a fixed or label-imbalanced schedule. Existing fixed-scale
  rivals and window tests cover it.

### Marker positions

- **Inherited choice:** a four-phase mostly fixed layout schedule intended to
  break rightmost-position, height-parity, and color-parity shortcuts.
- **Observed problem:** over 25,600 generated inputs, two different no-count
  rules predicted the scale perfectly: adjacent/full-span geometry and number
  of contiguous marker runs.
- **Alternatives considered:**
  1. Swap one or two phases. This broke the first heuristic but created a
     perfect component-count proxy.
  2. Use a four-phase all-adjacent/all-wide pattern. This removed one proxy but
     left a depth-two span/min-gap rule.
  3. Sample unconstrained random combinations. This increased support but could
     leave a short teaching window with no counterexample to a plausible rival.
  4. Use a constrained eight-slot schedule and test every lesson window.
- **Decision:** option 4. Ordinary phases cross the two labels with adjacency,
  contiguous-run count, span, gap sizes, edge contact, and rightmost position.
  Canonical `[0,2]` and `[0,2,4]` marker layouts remain ordinary defaults.
  Medium shifting and hard mirroring are retained.
- **Probes:** named rival window tests, semantic witnesses, the 25,600-grid
  no-count census, and the final semantic lesson gate.
- **Limitations:** bounded layouts still allow multivariate reconstruction of
  the marker count. That is acceptable when it is logically equivalent to
  counting; a future hard rival must have a legal disagreement example.

### Body color, shape, and placement

- **Inherited choice:** one connected non-rectangular object in color `2..9`,
  chosen from eight tight masks and placed below an empty separator row.
- **Original rationale:** expose crop texture and decouple color parity while
  preserving a small output.
- **Alternatives considered:** broaden body grammar during this review;
  rejected because no body-grammar defect was found and it would confound the
  marker-schedule experiment.
- **Decision:** unchanged.
- **Probes/failure modes:** exact override observability, canonical mirror tests,
  connectivity/one-color checks, solid-bounding-box rival, and the existing
  distribution/grammar batteries.

## Semantic contract choices

Three reproduced marker rules were added to `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`, with paired witnesses in
`SEMANTIC_WITNESSES` and `WITNESS_RIVALS`:

- `marker_geometry_scale` / `marker_geometry_decoupling`;
- `marker_component_scale` / `marker_component_decoupling`; and
- `marker_span_gap_scale` / `marker_span_gap_decoupling`.

The original rationale for not declaring these rivals is unknown; they were not
present in version 4.0.0. Making them executable prevents a future layout edit
from silently restoring the same correlations.

## Lesson size

- **Inherited choice:** `EXAMPLES_NEEDED = 3`.
- **Failure found:** with the new rival declared, the first after semantic run
  found 3/12 unidentifiable lessons. All started at sample index 22; the
  span/min-gap rule fit all three demos but disagreed on the query.
- **Alternatives considered:** distort marker layouts further so every
  three-draw window refutes the rival, or use the existing schedule guarantee
  of one refutation in every four draws.
- **Decision:** set `EXAMPLES_NEEDED = 4`. This is the smallest demonstrated
  window with the required guarantee and does not sacrifice layout coverage.
- **Probe:** an exhaustive test over every start in `0..23`, four difficulty
  modes, and four seeds checks all three marker rivals within the declared
  lesson length.

## Racket rule

- **Decision:** unchanged.
- **Rationale:** canonical execution, the Python mirror, and Racket smoke tests
  all agreed. The defect was in the generated input distribution, not output
  semantics.

## Reusable tooling

`workspace/marker_shortcut_probe.py` was added so future agents can repeat the
causal-statistic ablation rather than rely on hand-written guesses. It has
regression tests for exact-feature discovery, exclusion of explicit marker
count, small-sample splitting, and JSON serialization. Scikit-learn is optional;
without it, exact and named-rival checks still run.
