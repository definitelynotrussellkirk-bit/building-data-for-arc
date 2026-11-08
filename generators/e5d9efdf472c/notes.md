# Working notes: e5d9efdf472c

## 2026-10-02 review-b7a0e59aa1c81837

The v3 curriculum was semantically correct and all inherited checks were green,
but each difficulty band emitted only four fixed joint tuples of
`(grid_h, grid_w, orientation, gap, decor_pattern)`. Seed changes moved colors
and coordinates without changing that rule-relevant tuple. Version 4 keeps the
same sparse canonical scene family and the same four-example causal curriculum,
while sampling non-anchor dimensions and gaps within the declared ranges. One
of every four default samples remains an exact canonical-linked profile.

The separated-pair slot now guarantees that the irrelevant repeated-color pair
is strictly farther apart than the magenta pair. This refutes both the existing
"connect every repeated color" rival and the stronger canonical-fitting rival
"connect only the longest aligned repeated color". The latter fits all five
canonical examples because their only repeated decoration is adjacent and
shorter than the magenta span.

Measured over 1,600 default draws per band, the number of distinct semantic
axis tuples rose from 4 to 62 (easy), 160 (medium), and 163 (hard). Every one of
400 short-separated samples per band had a longer decoration pair and refuted
both canonical-fitting rivals. The full after battery passed 12/12 stages; the
strict-canonical fraction changed from 350/600 to 182/600 while remaining above
the declared 20% floor. The Racket rule and canonical/base authorities were not
changed.

Retained limitations: scenes remain sparse and use only one irrelevant
decoration color, by design and in line with the prior canonical-anchored scope
note. The stronger length rival is guaranteed only in the default curriculum;
explicit axis overrides remain free to request any valid combination.
## Current reviewer considerations

Source SHA-256: `c1ad050709b86807dc9ac28272891a6f782ec5885dd4c88c3b657c4f6f40f447`.

# Decisions: e5d9efdf472c

## D1 — Keep the selected Racket rule unchanged

- **Original rationale:** retained evidence says the selected canonical source
  and active base authority are synchronized; the rule matches all five
  canonical pairs.
- **Alternatives considered:** rewrite or simplify the Racket program; alter the
  canonical row to encode a broader task.
- **Probe/evidence:** before and after authority-sync passed; rule smoke matched
  the Python semantic mirror 120/120 with no crash or mutation.
- **Failure mode avoided:** changing correct authority while trying to solve a
  generator-distribution defect.
- **Limitation:** this review does not claim the canonical task itself has no
  other human-plausible interpretation beyond the tested rivals.

## D2 — Preserve the sparse canonical scene family

- **Input choice:** zero background, exactly two magenta markers, one sparse
  irrelevant decoration color, no cyan in inputs.
- **Original rationale:** prior retained note `canonical_anchored_sparse_scope`
  explicitly rejects speculative dense-layout widening; all canonical examples
  are sparse.
- **Alternatives considered:** multiple decoration colors, dense noise, objects
  crossing the target segment, or unrelated geometric motifs.
- **Probe/evidence:** canonical acceptance 5/5; after distribution, semantic,
  grammar, and rule-smoke gates all pass.
- **Failure mode avoided:** creating visually diverse but semantically
  unsupported inputs.
- **Limitation:** models are not trained here against dense clutter or multiple
  irrelevant color classes.

## D3 — Decouple grid dimensions from a four-row lookup table

- **Input choice:** non-anchor defaults sample dimensions within band ranges:
  easy `h=7..8, w=8..10`; medium `h=7..10, w=8..11`; hard
  `h=8..11, w=9..12`. Canonical-anchor samples use one of the exact five
  canonical-linked profiles.
- **Original rationale:** v3 hard-coded all five semantic axes together; seed
  changes did not alter the joint semantic tuple.
- **Alternatives considered:** independently sample every axis without a
  curriculum; add many more hand-written profiles; widen dimensions beyond
  declared bounds.
- **Probe/evidence:** failing regression observed 4 tuples in easy; final probe
  measured 62/160/163 tuples across easy/medium/hard. Override boundaries and
  all 16,110 contract draws pass.
- **Failure modes:** independent unconstrained sampling could omit required
  lesson evidence; hand-written profiles would preserve hidden correlations.
- **Limitation:** the canonical-anchor role can use a canonical dimension from
  outside the non-anchor band range, intentionally preserving exact canonical
  support in every band.

## D4 — Use four semantic curriculum roles

- **Input choice:** `long_single`, `canonical_anchor`, `short_separated`, and
  `middle_adjacent`, indexed by `sample_index % 4`.
- **Original rationale:** the inherited generator already used a four-example
  lesson and declared `EXAMPLES_NEEDED = 4`.
- **Alternatives considered:** fully IID sampling; a longer curriculum; fixed
  numeric profile IDs.
- **Probe/evidence:** all four start residues in every band pass
  `lesson_identifiable`; semantic gate reports all 12 requested lessons
  identifiable.
- **Failure mode avoided:** a random four-demo lesson omitting one orientation,
  the canonical adjacent cue, or the repeated-color counterexample.
- **Limitation:** sample-index residue remains semantically meaningful by design;
  what changed is that each role now contains seed-varying geometry.

## D5 — Pair orientations within each cycle

- **Input choice:** one seed-stable orientation for `long_single`; the
  `short_separated` role uses the opposite orientation; other roles vary
  independently or inherit their canonical profile.
- **Original rationale:** every four-demo window must show both horizontal and
  vertical branches.
- **Alternatives considered:** IID orientation for every sample; fixed
  orientation per residue.
- **Probe/evidence:** regression requires both orientations in every band;
  semantic gate fires horizontal and vertical witnesses and verifies their
  respective rivals.
- **Failure mode avoided:** an unlucky four-example lesson containing only one
  branch.
- **Limitation:** this introduces a purposeful within-cycle relation between two
  roles; it is pedagogical coverage, not an attempt at IID data.

## D6 — Preserve explicit short, middle, and long gap roles

- **Input choice:** short gap `1`; middle gaps `2..3`; long gaps `4..5`; the
  canonical anchor retains its exact canonical gap.
- **Original rationale:** inherited lesson checks require a short boundary, a
  long branch, and at least three observed gap values.
- **Alternatives considered:** IID `1..5`; fixed one gap per role and band.
- **Probe/evidence:** every tested four-sample window spans short and long gaps;
  final signatures cover all gap values `1..5`; `gap five only` is refuted.
- **Failure mode avoided:** learning that cyan fill occurs only at one distance.
- **Limitation:** no zero-gap/adjacent marker case is generated because the
  canonical rule family requires at least one interior cell.

## D7 — Keep all three decoration topologies, but make the key one causal

- **Input choice:** `single`, `adjacent_pair`, and `separated_pair`. In the
  default short-separated role, decoration distance is at least
  `marker_gap + 2`, hence strictly greater than marker endpoint distance.
- **Original rationale:** adjacent repeated color is a canonical cue; separated
  repeated color is the smallest counterexample to “connect every repeated
  color.”
- **Alternatives considered:** remove repeated decorations; allow arbitrary pair
  lengths; add a second decoration color.
- **Probe/evidence:** the red test first showed no causal-distance observable;
  an intermediate probe found only 308/400, 294/400, and 300/400 dominant
  distractors. Final probe is 400/400 in every band.
- **Failure modes:** removing repeated colors makes the shortcut untestable;
  arbitrary lengths leave “connect only the longest pair” alive on some
  lessons.
- **Limitation:** explicit overrides can intentionally request a separated pair
  without the default length relation.

## D8 — Add the strongest surviving canonical-fitting rival

- **Input choice:** executable rival “connect only the longest aligned repeated
  color,” with an explicit semantic witness
  `longer_decoration_counterexample`.
- **Original rationale:** all canonical examples contain a long magenta pair and
  only an adjacent repeated decoration; therefore the rival changes exactly one
  pair and fits the entire canonical set.
- **Alternatives considered:** document the rival only; rely on the broader
  “connect every repeated color” rival; add a synthetic rival that does not fit
  canonical examples.
- **Probe/evidence:** red test failed because the rival did not exist; final test
  proves 5/5 canonical fit and disagreement on 36 generated witnesses. Semantic
  gate verifies the eighth rival claim on 60 sampled cases.
- **Failure mode avoided:** a prose-only shortcut claim that can drift from
  executable behavior.
- **Limitation:** the rival chooses a deterministic maximum; tie cases are not
  the discriminator used by this curriculum.

## D9 — Expose pair-distance observables

- **Input choice:** `marker_distance`, `decor_distance`, and
  `decor_longer_than_marker` are returned by `semantic_observables`.
- **Original rationale:** witness predicates should assert the causal distinction
  directly rather than infer it from profile labels.
- **Alternatives considered:** inspect coordinates only inside tests; add another
  schedule role flag.
- **Probe/evidence:** focused tests and semantic gate consume the observable;
  final census records 1,200/1,200 causal short-separated cases.
- **Failure mode avoided:** a profile named “counterexample” silently ceasing to
  be one after placement changes.
- **Limitation:** distance is Manhattan distance for aligned pairs; diagonal
  decorations are outside the declared topology.

## D10 — Retain override semantics

- **Input choice:** declared overrides still select exact dimensions,
  orientation, gap, and decoration pattern within existing valid ranges.
- **Original rationale:** the repository contract treats overrides as a separate
  combinatorial interface and tests all legal combinations.
- **Alternatives considered:** force the stronger length relationship even when
  callers explicitly override axes; reject combinations that do not serve the
  default lesson.
- **Probe/evidence:** override gate passed 16,110/16,110 draws and 179 override
  cases with no explicit-combination rejection.
- **Failure mode avoided:** silently changing an established caller-controlled
  contract to satisfy a default-curriculum invariant.
- **Limitation:** an override-generated episode can be valid yet weaker as a
  teaching example; callers assembling lessons from overrides must make their
  own identifiability check.
