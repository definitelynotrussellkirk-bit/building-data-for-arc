# Current notes: 2692a3e47a66

## 2026-10-19 — review-cc6df0b7bf591ff4

Original family: ARC training:22208ba4. Canonical generator VERSION remains
`3.0.1`; repaired source SHA-256 is
`ff79193bed2cc537c82a56abd6235304e2f2fb791eda67050b68bb84b048f328`.
The normalized canonical Racket rule hash remains `f5a9e05539e5`.
This review changes no reference rule, authority, catalog, or approval record.

### Rule and canonical input distribution

Use the modal background (canonically 7). Count disconnected components of each
foreground color in the original input. Colors with fewer than two components
stay unchanged. Move every component of each repeated color diagonally inward
by its own bounding-box height and width, clearing that color's original cells
and painting in the canonical ascending-color order. Same-color translated
components may merge: four side-2 corner blocks on a 7x7 grid become a central
3x3 square. The previous blanket non-overlap claim was too strong.

The inherited canonical sampler intentionally retains four solid corner
squares, side lengths 1–4, unique-modal background 7, foreground palette
(1,2,3,4,5,6,8,9), and dimensions 7–30. Its four observable profiles cycle in
sample-index order: all_same_uniform, triple_single_mixed,
pair_singletons_uniform, two_pairs_mixed. The all-same profile defaults to a
16x16 canonical support anchor; exact dimension overrides take precedence.
These are retained input choices, not newly inferred universal rule limits.

### Concrete canonical repairs

- Reject Boolean/noninteger seeds, Boolean/noninteger/negative sample indices,
  and numeric difficulty values before constructing the generation context.
  Valid difficulty is None, easy, medium, or hard; negative integer seeds remain
  supported. This resolves the recovered before battery's 45 strict-scalar
  warnings.
- Treat `scene_profile=None` like an omitted override. Previously key presence
  broadened profile choices despite GenCtx's None-as-omission convention. At
  seed 71, index 0, medium, omission selected all_same_uniform while explicit
  None selected triple_single_mixed. The focused pre-repair sample had 14/16
  mismatches.
- Keep VERSION 3.0.1 because it salts the deterministic RNG. All 108 retained
  legal scheduled/exact-override calls have identical pre/post grid hashes.
  Source hashes distinguish this repair; preserving the version is not an
  assertion that the old approval covers new source bytes.

Regression tests live in tests/test_call_contract_2692a3e47a66.py. Exact
counterexamples are under counterexamples/review-cc6df0b7bf591ff4/. The return's
checks/call-contract/ retains genuine red (29 failed, 6 passed), green (35
passed), original source, and continuity evidence.

### Teaching policy and shortcut limits

The canonical export policy is four consecutive ordered demonstrations followed
by the next generated query. Every cyclic four-demo window contains both
required witnesses. The actual declared rivals are
move_only_modal_object_color and move_repeated_blocks_by_one_global_size; both
fit all five canonical pairs. two_pairs_mixed refutes the first and
triple_single_mixed refutes the second.

Arbitrary single-query rotations are not supported by this four-demo policy.
A seed-71 probe of three bands and all four starts found 12/12 ordinary lessons
identifiable against both rivals, but 9/60 rotations left the modal-color rival
alive and wrong on the query. The exact medium lesson has demos at indices
[0,1,2,4] and query 3. Retain ordering, or explicitly add a second two-pair witness
before permitting that downstream assembly. A finite rival check does not prove
unique induction against all possible rules. Final source-bound Racket/census
counts and commands are in the accompanying REVIEW.md and RESULTS.json.

### Separate proposed parametric prototype

workspace/parametric/prototype.py and its README provide a runnable extension.
Choose min_repeat from {2,3,4} and step_blocks from {1,2} once per episode.
The canonical default (2,1) emits the exact original Racket program. Object
roles, component counting, inward direction, per-object size scaling, and
singleton retention remain recognizable; thresholds and distance alter the
executed transformation rather than merely changing appearance.

The prototype sampler uses a deliberately narrower 25–30 safe geometry envelope
for all six settings, variable square sizes/colors, and six distinct demos
(two multiplicity witnesses each for 2, 3, and 4) plus one query. Racket labels
all examples; all six candidate settings are checked under production and every
single-query holdout. Public challenges omit settings, programs, and query
labels, and are withheld when checks fail. Private plans and receipts preserve
reproduction state. The full canonical default is separately checked against
all five canonical pairs, including inputs outside that safer sampling subset.

The 49 retained successful holdouts concern those six parameter settings only.
A separate saved-default-episode probe (seed 20261019, episode 0, settings 2/1)
finds one of seven rotations ambiguous against the actual canonical modal-color
rival: holding out the sole two-pair input at index 5 leaves six matching demos
and a query disagreement in ten cells. The designated production query at index
6 is distinguished. Preserve the exported six demos and seventh query; broader
rotation support is not established. Exact evidence is in the return's
checks/parametric/canonical-rival-scope/.

This is a proposed authoring prototype, separate from the selected canonical
execution path and from training/variant approval. It does not claim arbitrary
shapes, backgrounds, object counts, untested settings, or universal induction.

### Prior rationale and provenance

The 2026-10-02 notes describe the earlier four-corner repair and D1–D13 choices.
Those notes were used as leads, not counted as current measurements. The pinned
prior review index names review-830549bca7fa4807:v0001 as independently checked;
that retained receipt is not fresh approval of the repaired source. The final
public apply receipt reports catalog_approved=false and train_safety=reviewed_safe;
these are separate fields. This review changes neither approval nor admission. The current
return's DECISIONS.md records retained input choices, alternatives, the two new
contract decisions, prototype scope, and known failure modes. Historical
associated notes remain in evidence/associated_notes.jsonl.
## Current reviewer considerations

Source SHA-256: `ff79193bed2cc537c82a56abd6235304e2f2fb791eda67050b68bb84b048f328`.

# Decisions — review-cc6df0b7bf591ff4

## Objective, provenance, and order of work

The assigned original family is training:22208ba4, task 2692a3e47a66.
The requested priority was a small parametric extension first. The separate
prototype and initial tests were implemented before the canonical source was
edited. The prior review index names review-830549bca7fa4807:v0001 as
independently checked; its historical notes were leads, not present-source
measurements. The older two-singleton implementation rationale is unknown.
The pinned generator for this review was already the richer four-corner repair.

Final canonical source: ff79193bed2cc537c82a56abd6235304e2f2fb791eda67050b68bb84b048f328.
Baseline: afa164c22fc4a1bf696a2c6c7dcc6531cec4d7214700305a86178dff3888cb94.
The selected Racket rule and all shared/catalog/approval sources are unchanged.

## Retained canonical input choices

| Choice | Rationale and rejected alternative | Evidence or limit |
|---|---|---|
| Exactly four solid corner squares | Preserve demonstrated object roles and inward directions. Interior, hollow, or arbitrary components would add an unsupported morphology problem. | All five canonical inputs accepted; final semantic gate 600/600 strict draws. |
| Background 7, uniquely modal | Matches the demonstrated palette and makes the reference mode operation unambiguous. Random backgrounds would widen visual support without addressing this review's defects. | Canonical support and structural tests; modality remains an input invariant. |
| Foreground palette 1,2,3,4,5,6,8,9 | Excludes background aliasing and retains inherited nonzero foreground convention. Adding 0 is executable but outside the selected visual grammar. | Existing palette/diversity/override checks retained. |
| Square sides 1–4, mixed sizes | Per-object size must determine displacement. A single global side leaves a canonical-fitting shortcut alive. | Actual global-size rival fits 5/5 canonical pairs; mixed-size demonstrations refute it. |
| Dimensions 7–30 with geometry-dependent caps | Retain rectangular and scale variation while maintaining input separation and modality. Fixed coordinates or a single canvas shape would narrow the task. | Exact overrides cover 7x7, 17x19, 30x30 in continuity checks. |
| Four observable color/size profiles | [4], [3,1], [2,1,1], and [2,2] expose movement, singleton retention, per-object distance, and multiple repeated colors. | Actual production declarations supply both required witnesses. Pure random multiplicities can omit them. |
| Deterministic four-sample profile cycle | Every consecutive ordered four-demo window contains both witnesses. Frequency alone is not a lesson guarantee. | All four cyclic starts at seed 71 across three bands: 12/12 refute both declared rivals. |
| A 16x16 all-same anchor every fourth sample | Retain intentional canonical-profile support while allowing the other three profiles broader dimensions. | Final floor: 19/60 exact and 47/60 envelope. This anchor is overrepresented deliberately. |
| Three exact public overrides | grid_h, grid_w, scene_profile remain observable. Unsupported keys should raise instead of silently changing another knob. | Existing task tests and final override gate; new None-equivalence regression. |
| Structural validation independent of generation | Accept canonical inputs and reject off-grammar inputs rather than merely recognizing sampled parameters. | Final self-check and strict profile gates; no arbitrary-Racket-domain claim. |

The old claim that all moved objects remain non-overlapping was reversed.
Same-color translations can merge lawfully. The exact 7x7 example has sixteen
foreground input cells and nine foreground output cells; selected Racket
confirmed that output. We corrected the notes rather than changing the rule
or imposing area conservation. See checks/main-witnesses/comparison.json.

## Two canonical contract repairs

**R1 — Reject scalar coercion.** The recovered before battery found 45 warnings
across its scalar contexts. Boolean, float, and string seeds/indices had reached
integer coercion in generation; negative indices and numeric difficulty values
were also accepted. Validate before constructing GenCtx. Seeds remain signed
integers; sample indices are nonnegative integers; difficulty is None, easy,
medium, or hard. Accepting numeric difficulty was rejected because it is not the
advertised public contract and hides malformed calls.

**R2 — Make None omission consistent.** GenCtx treats a None override as absent,
but the generator broadened its profile pool whenever the key existed. Change
that condition to test a non-None value. The exact seed-71/index-0 medium witness
changed from the scheduled all-same profile to triple-single when None was
present. The initial 16-pair probe found fourteen mismatches; final comparison
finds zero, with identical grids in all sixteen cases.

Tests were written and run against the untouched source first: 29 failed and
6 passed. After the narrow repair all 35 pass. The separate original and repaired
108-call manifests match every valid grid hash. Keep VERSION 3.0.1 because it
salts the RNG; a version bump would redraw valid calls. The final source SHA,
not an inherited approval receipt, identifies the repaired implementation.

## Canonical lesson assembly

Use four consecutive demonstrations followed by the next generated query.
The larger public census uses the production sampler, actual accepted sample
indices, two unique declared rivals (exposed through three declaration maps),
and a reporting modulus of four. It is not a new sampler or an exhaustive seed
proof. Exact final counts are in REVIEW.md and the per-band compressed census.

Arbitrary query rotation is not supported. The seed-71 medium lesson with
training indices [0,1,2,4] and query index 3 omits the only two-pair witness;
move_only_modal_object_color then fits every demo and differs from Racket in
four query cells. Retain ordering. If a future assembler permits arbitrary
holdouts, add another independently varied two-pair witness and verify that
new assembly. Expanding the canonical demo count merely to pass a diagnostic
was rejected because the current ordered policy already teaches both rivals.

## Separate proposed parametric extension

Two frozen episode-level settings change executed behavior:

| Parameter | Domain | Canonical default | Meaning |
|---|---|---|---|
| min_repeat | 2, 3, 4 | 2 | Minimum disconnected component count for a color to move. |
| step_blocks | 1, 2 | 1 | Scale each object's inward displacement by its own dimensions. |

The default (2,1) emits the exact canonical registration text. All five canonical
pairs are checked through Racket, including smaller/overlapping cases outside
the prototype sampler. Color counting, object roles, inward direction, and
per-object size remain invariant. A mere palette/size reskin was rejected because
it would not alter the executed transformation. Thresholds above four collapse
this four-object grammar to identity; distance zero similarly removes its main
operation. The six chosen settings are small and interpretable.

The prototype independently varies height and width in 25–30, sides 1–4,
colors, placement of repeated colors, and layouts. This narrower geometry keeps
every possible inward footprint within a 12-cell corner envelope for both
movement scales. Opposite envelopes are disjoint because each dimension is at
least 25. We did not change the canonical generator's 7–30 support to make the
prototype convenient. Mixed repeated objects have unequal sides, so component
count and own-size distance remain visible rather than reducing to pixel area
or one global block size.

Choose settings once by the deterministic episode seed, or explicitly once for
an evidence episode. Materialize six distinct demonstrations, with two witnesses
each for multiplicities 2, 3, and 4, plus one query. Execute all six Racket programs
on every input. Compare every candidate at every single-query holdout using
those saved labels; these comparisons are not extra samples or Racket calls.
The retained seven episodes cover all six explicit settings and one seeded
selection: 49 distinct inputs, 299 actual Racket applications, and 49 successful
placements against the six parameter settings.

**Broader-rival scope matters.** The default episode also refutes both actual
canonical rivals in its designated production ordering. However, holding out its
sole [2,2] pair (index 5) lets the modal-color rival fit the other six pairs and
miss Racket by ten cells. Thus the 49 parameter-family rotation checks do not
certify arbitrary rotations against broader algorithms. Keep the designated
six demos and seventh query. The exact scope probe and held-out lesson are in
checks/parametric/canonical-rival-scope/. No universal induction claim is made.

## Public export and failure evidence

Public challenges contain only demonstration inputs/outputs and query inputs.
Settings, program text, query labels, seeds, traces, and source hashes are private.
Public UUID filenames and independently shuffled export order avoid revealing
the fixed setting enumeration. Seeded puzzle content is reproducible; presentation
identifiers/order intentionally use separate fresh randomness.

Reject ambiguous or mirror-mismatched episodes before public export, returning
public=None while keeping private diagnostics. Persist the request and all input
plans before starting Racket. Genuine red tests exposed missing preflight and
startup-failure records; corrected runs retain the useful evidence. The final
26-test suite and 299-application CLI both pass. The prototype is proposed and
task-local; it does not alter the canonical runtime API or approve variants.

## Verification and environmental decisions

The shared disk and inode space were exhausted, so a private temporary namespace
held the verified extraction. All 78,747 WORK manifest files plus two outer files
were verified before the single assignment draw. Hash-equal immutable references
were deduplicated; later verified cold copies were temporarily evicted with the
unchanged original ZIP as backing. Their restoration manifest is retained, and
all required bytes are restored before the builder validates unchanged sources.

Preserve interrupted batteries, the rejected unsafe resume, and the combined
census's lost-Racket-state failure. Do not count partial runs as aggregate passes.
Fresh complete runs provide the final verdicts. Separating the census into one
fresh process per difficulty band preserves the sampler while limiting accumulated
runtime state. Focused replay uses the official runtime-closure option; that is
explicitly partial extraction, followed by tests in the fresh copy's own environment.
The official replay applied the frozen patch and matched all 15 changed files.
A separate fresh task-test stage passed all 75 tests with zero skips; the final
source/solve binding verifier also exited 0. The additional temporary eviction
of unselected references required for that replay was reversed: an independent
readback verified all 63,721 restored paths, hashes, sizes and modes with no failures.

Both drawn audits are findings only. No audited target source was edited. Solves
retain actual exposure declarations and unknown masked-query correctness. The
complete handoff includes exact command records, logs, source hashes, and the
unchanged assignment; the official builder supplies INTAKE.json.
