# Working notes: `aae03e82a263`

## Review identity

- Assignment: `review-6364b207c4fc11dc`
- Canonical rule hash: `69eaaa031800`
- Baseline generator SHA-256: `e52b21eb6b8d4e687b360b690188f821fe2be78165ac745cf3edb2e879ccab50`
- Reviewed generator version: `3.0.0`
- Reviewed generator SHA-256: `49ec4957f76c35d3c8eb2c15d37d3f84c06bebd928eb2f194e87fc89fb53315a`
- Canonical Racket semantics changed: **no**
- Selected archival `target_code` changed only to become byte-identical to the canonical source.

No prior task review index was available. `evidence/associated_notes.jsonl` was empty.

## Intended rule

Find the color-6 objects using 4-connectivity. Their cell areas are distinct and
the object count is odd. Sort by cell area, select the median object, normalize
it to its tight bounding box, transpose its occupied coordinates, and return the
tight color-6 crop on a zero background.

The canonical inventory has five labelled pairs. Every canonical input has three
objects with areas 4, 5, and 6, so two wrong rules fit all canonical pairs:
selecting the second-smallest object and selecting the five-cell object. Those
are retained explicitly in `counterexamples/canonical_shortcuts.json`.

## Baseline findings

The required before battery finished with 6 green, 2 advisory, and 4 failed
stages (`checks/before/checks/aae03e82a263_before_battery_summary.json`).

- `RULE_HASH` was absent and exact authority text diverged: canonical/raw source
  was semantically equivalent to, but not byte-identical with, selected
  `target_code`.
- The override contract accepted 50,670/50,670 draws but recorded 56,668
  findings across 563 cases. Grid dimensions were routinely ignored,
  `n_objects` was not observable, pseudo-axes were never probed, unknown keys
  were accepted, and negative textures were mixed into ordinary generation.
- `self_check` accepted empty, one-object, tied-area, even/ambiguous and
  wrong-palette inputs. Static reproducers are retained in
  `counterexamples/degenerate_impostors.json`.
- Medium and hard had zero canonical-profile support in 20 draws each; pooled
  envelope support was 8/60.
- No strict-profile, witness, rival, canonical-shortcut, or lesson-identifiability
  contract existed.

## Decisions implemented

### Canonical authority remains singular

`RULE_HASH` is pinned to `69eaaa031800`; `rule_mirror` is diagnostic only. The
selected base record now uses the exact canonical text for both `raw_code` and
`target_code`. Rule smoke and authority synchronization validate the Racket
source.

### A narrow, honest domain replaces nominal flexibility

Ordinary and override generation now support exactly:

- dimensions `12|13|18` independently on each axis;
- object counts `3|5`;
- median selected area `4..6`;
- colors `{0, 6}`;
- pairwise-distinct areas and 8-neighbor separation between objects.

`observe_overrides` reports every exact semantic value. Unknown, mistyped and
out-of-domain controls fail loudly. The initial repair used the full integer
range 12..18, but the override checker expands small ranges and tests every
cross-axis pair, producing 147 cases and an unnecessarily long quadratic
matrix. The final explicit dimension set preserves canonical anchors and broad
18-cell canvases while reducing the matrix to 59 cases. This decision reversal
is covered by `test_dimension_domains_bound_the_quadratic_override_matrix`.

### Constructive five-slot curriculum

The deterministic schedule is:

1. 3 objects, median area 5, ascending reading order, canonical anchor;
2. 5 objects, median area 4, target last;
3. 5 objects, median area 6, target first;
4. 3 objects, median area 4, target last;
5. 5 objects, median area 5, target second.

Target shapes are asymmetric sparse polyominoes; decoys are compact. Placement
is bounded backtracking with exact post-construction validation and no fallback
that changes requested controls. `EXAMPLES_NEEDED = 4`: any four pairs from the
five-slot lesson refute all declared competitors, so arbitrary query rotation is
supported.

### Executable semantic diagnostics

The generator declares and tests seven rivals: smallest, largest,
second-smallest, reading-order middle, bounding-box-area middle, fixed five-cell
selection, and median-without-transpose. `fixed_size_five` and
`second_smallest` are separately declared canonical shortcuts and verified to
fit every canonical pair before generated lessons refute them.

`lesson_identifiable` scores the actual demonstrations rather than trusting
schedule labels. `strict_canonical_like`, semantic witnesses, mutation fixtures,
rule parity, exact controls, global-RNG purity and distribution breadth are
covered by 32 portable task-local tests.

## Verification

Final generator/authority subject `8bd422795d041b4e` passed all 12 battery
stages (`checks/after-battery/checks/aae03e82a263_after_battery_summary.json`).
The strict override stage accepted 5,310/5,310 draws over 59 cases with zero
findings or warnings. Profile-floor coverage was exact in every band: 12/20
easy, 5/20 medium and 11/20 hard.

The final portable task stage passed 32/32 tests
(`checks/task-tests-final/result.json`). A larger production census materialized
300 lessons (100 per band), 1,500 labelled pairs and 1,500 held-out query
rotations with 1,500 unique inputs, zero ambiguity, zero hook warnings and zero
scoring/materialization errors (`checks/lesson-census.json`).

The post-repair visible-only solver passed all four displayed examples on its
first implementation. Earlier rule exposure was declared `yes`; no reference
source was consulted during that solve.

## Known limits

- The rival library is finite; passing it does not prove unique induction against
  every imaginable hypothesis.
- Constructive placement is tested extensively but not formally proven for every
  integer seed.
- The supported dimension domain is deliberately discrete rather than every
  integer from 12 through 18.
- Generated objects are color 6 only, matching the canonical task. Palette
  generalization is not claimed.
- Approval/train-safety remains a maintainer decision; passing checks does not
  change catalog approval automatically.
## Current reviewer considerations

Source SHA-256: `49ec4957f76c35d3c8eb2c15d37d3f84c06bebd928eb2f194e87fc89fb53315a`.

# Decisions for `aae03e82a263`

## D1 — Preserve the canonical rule

**Choice.** Keep the canonical Racket semantics unchanged and pin
`RULE_HASH = 69eaaa031800`. Make the selected archival `target_code` byte-identical
to canonical `program_solution`/`raw_code`.

**Rationale.** All five canonical pairs were solved by both prior sources; the
failure was duplicated source text, not semantic disagreement. One exact source
reduces authority drift.

**Alternative rejected.** Rewrite or simplify Racket. There was no demonstrated
rule defect, and changing authority would expand the review beyond the generator.

**Probe/failure mode.** Rule smoke, exact authority synchronization, and focused
hash/source equality tests. Future source formatting changes must rerun all three.

## D2 — Replace broad nominal controls with an honest exact domain

**Choice.** Expose only dimensions `12|13|18`, object counts `3|5`, and median
areas `4..6`. Report realized values through `observe_overrides`; reject unknown,
boolean, string and unsupported values.

**Rationale.** The baseline declared much broader ranges and overlapping texture/
palette controls while ignoring dimensions in practice. That yielded 56,668
findings over 50,670 accepted draws. A narrow falsifiable contract is more useful
than flexibility that cannot be honored.

**Alternatives rejected.** Preserve every old axis; silently coerce values; or
attempt all dimensions 11–24 and object counts 3–5. These options either retain
inert controls or spend data budget on profiles with no task-specific evidence.

**Decision reversal.** The first repair declared every integer dimension 12..18.
The override checker expands short ranges and then builds a pairwise cross-axis
matrix, producing 147 cases and an impractically long foreground run. The final
explicit set `12|13|18` retains canonical anchors and a large-canvas profile while
reducing the matrix to 59 cases. A focused regression pins this bound.

**Probe/failure mode.** Strict override stage across all bands/seeds, plus direct
invalid-value and global-RNG tests. Future axis additions need an observer and a
bounded interaction matrix.

## D3 — Require a unique median

**Choice.** Accept exactly three or five objects with pairwise-distinct cell
areas, canonical colors `{0,6}`, majority-zero background, and no contact between
objects even diagonally.

**Rationale.** The rule's median is only unambiguous for an odd count with no area
ties. Separation prevents two intended objects from merging and prevents
incidental diagonal grouping from becoming a texture cue.

**Alternatives rejected.** Define tie-breaking by reading order; allow one object;
allow even object counts; or keep negative fixtures in ordinary generation.
Those change or trivialize the task rather than teach it.

**Probe/failure mode.** Static empty, single-object and tied-area counterexamples,
wrong-color mutation, canonical acceptance, and every generated grid through
`self_check`.

## D4 — Teach beyond the canonical shortcut manifold

**Choice.** Use a deterministic five-slot schedule with object-count, median-size
and reading-order profiles:

1. `(3, 5, ascending)`
2. `(5, 4, target_last)`
3. `(5, 6, target_first)`
4. `(3, 4, target_last)`
5. `(5, 5, target_second)`

Require four demonstrations and permit any one slot to be the query.

**Rationale.** Canonical data always has areas 4/5/6, so “choose five cells” and
“choose second-smallest” are perfect canonical shortcuts. Varying object count,
median size and target order directly breaks them while retaining recognizable
canonical anchors.

**Alternatives rejected.** Random independent examples with no lesson contract;
three demonstrations; or canonical-only replication. Those can leave a plausible
wrong rule consistent with every demo.

**Probe/failure mode.** `CANONICAL_SHORTCUTS` must first fit all five canonical
pairs, then every four-of-five lesson rotation must refute every declared rival.
The large census repeats this over 100 lessons per band.

## D5 — Make transpose causally visible

**Choice.** Select target shapes from asymmetric high-bounding-box-area
polyominoes and decoys from compact pools.

**Rationale.** A transpose-invariant target cannot distinguish the intended rule
from “select median and return unchanged.” Sparse asymmetric shapes make the
coordinate swap observable without adding colors or markers.

**Alternatives rejected.** Arbitrary connected shapes, which frequently include
symmetric examples; or a fixed target template, which enables memorization.

**Probe/failure mode.** `median_without_transpose` is executable and must be
refuted in every lesson rotation. Output diversity and shape tests guard against
collapse.

## D6 — Keep the mirror diagnostic and input-pure

**Choice.** Implement `rule_mirror` for high-volume tests, rivals and census
scoring while retaining Racket as authority.

**Rationale.** Thousands of semantic probes need a cheap deterministic oracle;
a second authority would be dangerous. Exact canonical parity and Racket stages
bind the mirror to the source of truth.

**Alternative rejected.** Call Racket for every local rival comparison or treat
the Python mirror as authoritative.

**Probe/failure mode.** Mirror parity on every canonical pair, rule smoke on
generated data, no input mutation, and authority sync.

## D7 — Fail loudly after bounded constructive search

**Choice.** Use deterministic bounded placement retries and raise with the
requested profile if no layout is found. Never silently alter controls.

**Rationale.** Silent fallback creates mislabeled metadata and defeats override
verification. Exact post-construction observation is cheaper than debugging
latent distribution drift.

**Alternative rejected.** Unbounded search, grid clipping, or reducing object
count/size on failure.

**Known limitation.** The tested domain is empirically robust but not formally
proved for every seed.
