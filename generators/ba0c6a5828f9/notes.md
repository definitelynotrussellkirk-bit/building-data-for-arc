# Working notes: ba0c6a5828f9

## Review lead and baseline

Prior return `review-8f1884f12a6bc9b2:v0001` was used only as a lead. Its main
claim—that a geometric-center shortcut fits the public examples but not the
intended domain—was rechecked against the pinned source rather than treated as
current evidence.

The retained before battery is under `checks/before/`. The pinned v2.1.2 source
had four blocking stages: lint, defect lint, override contract, and authority
source sync. It advertised eight controls while only sampling a subset, accepted
unknown override keys, exposed degenerate outputs through a nominal texture
axis, and generated no deliberate lesson schedule. The selected authority's
executable behavior matched canonical, but one nested `target_code` copy carried
an extra comment and was not exact-source synchronized.

## Repair hypothesis

The core teaching defect was not label correctness: the rule runner already
produced correct labels. The defect was observational equivalence. Public-like
centered/full-orbit scenes cannot distinguish either of these plausible rules:

1. use the geometric canvas center instead of the red cell;
2. skip a source marker whenever any rotated image is out of bounds.

Randomly widening dimensions and pivot positions did not guarantee that either
branch appeared in each assembled lesson. The repair therefore constructs four
observable semantic profiles rather than adding more random axes.

## Selected design

- `canonical`: centered 7×7/9×9, 2–3 markers, complete orbits;
- `off_center`: off-center red pivot, complete orbits;
- `clipped`: centered red pivot, at least one useful partial orbit;
- `mixed`: off-center pivot plus a useful partial orbit.

A seed-phased length-four schedule emits every profile in every consecutive
four sample indices. Since any three of these four include evidence against
both named rivals, all four possible three-demo/query rotations are executable
and testable. The only caller-facing override is the exact, pixel-observable
`profile` axis.

Geometry is constructive. Marker sources are chosen from distinct rotation
orbits. Clipped profiles require a partial orbit with at least two in-bounds
members, so the intended output is non-identity and differs from the
full-orbits-only rival. Off-center profiles are accepted only when their output
actually differs from the geometric-center rival.

## Authority decision

The canonical Racket rule and canonical puzzle row were not changed. The nested
`racket_target.target_code` copy in the selected base solution was synchronized
byte-for-byte to canonical `program_solution`; `racket_target.raw_code` already
matched. This is an authority bookkeeping repair, not a rule behavior change.

## Tests and reusable evidence

Task-local tests are in `tests/test_generator.py`. Their independent geometry
oracle lives in `workspace/reference_probe.py`; it deliberately does not import
production geometry helpers. The suite checks canonical pairs, exact authority
binding, all profile/band overrides, malformed inputs, 128 draws per band,
canonical-fitting rivals, all cyclic three-demo/query rotations, and purity.
The initial red run is retained as `checks/tdd-red.log`; the first green run is
`checks/tdd-green-attempt1.log`.

## Known limits

The two declared rivals are concrete, plausible, and public-example-fitting,
but finite rival checks do not prove unique induction over all possible ARC
programs. The generated manifold intentionally limits canvases to 7–14 and
source counts to 2–5; this bounds training complexity rather than the reference
rule's executable domain. The canonical rule remains the output authority.
## Current reviewer considerations

Source SHA-256: `dcd2f5b1601cbabe8655bd959879153513cfdbe58f2f6bb4b4dbde2a6cdd1886`.

# Decisions — `ba0c6a5828f9`

The goal was not to maximize superficial randomness. It was to make the intended
rotation rule inferable from each assembled lesson while keeping labels bound to
the selected canonical Racket authority.

## D1 — Preserve the canonical rule

**Choice.** Keep canonical `program_solution` and its behavior unchanged; pin
`RULE_HASH = "e28fcc7b8767"`.

**Original rationale.** The baseline did not document why it lacked a hash pin.
Behavioral checks already showed the Racket program solved canonical examples.

**Alternatives considered.** Rewrite or simplify the Racket program; move label
authority to the Python mirror.

**Probe.** Before/after rule smoke, canonical pair tests, mirror parity, Racket
lint, and exact authority sync.

**Why rejected.** No behavioral rule defect was found. Rewriting the authority
would add risk while failing to address the actual lesson ambiguity.

**Failure modes / limits.** Python mirror parity is sampled, not a proof over all
grids. The canonical Racket source remains authoritative.

## D2 — Replace generic random axes with one semantic profile axis

**Choice.** Remove `grid_h`, `grid_w`, `n_ones`, `palette_*`, `position_bias`,
`density`, and `texture` from the advertised override contract. Expose only
`profile ∈ {canonical, off_center, clipped, mixed}`.

**Original rationale.** Unknown. The baseline appeared to have been generated
from a broad generic axis template; several axes were singleton, unprobeable,
ignored, internally range-incompatible, or included deliberately invalid
fixtures as ordinary values.

**Alternatives considered.** Repair every old axis independently; leave dead
axes as diagnostic; add still more random controls.

**Probe.** Baseline override matrix, defect lint, exact per-profile task tests,
unknown-key probe, and final 450-draw override contract.

**Why selected.** A smaller observable contract is more useful than many nominal
knobs. Profile selection changes pixels and directly controls the two semantic
branches that matter.

**Failure modes / limits.** Consumers relying on undocumented old keys now get a
clear `ValueError`. That is deliberate contract tightening.

## D3 — Use four profiles, not two binary flags exposed independently

**Choice.** Define four joint states:

- `canonical`: centered, no clipping;
- `off_center`: off-center, no clipping;
- `clipped`: centered, clipping;
- `mixed`: off-center, clipping.

**Original rationale.** The baseline had no explicit semantic profiles.

**Alternatives considered.** Two independent `pivot_mode` and `clipping_mode`
axes; only two witness profiles; unrestricted random pivot and edge placement.

**Probe.** Independent profile classifier, exact overrides across every band,
rival relation matrix, and all cyclic lesson rotations.

**Why selected.** The four-state profile is pixel-observable, compact, and
makes the joint branch explicit. It avoids claiming arbitrary axis independence
while still covering all four combinations.

**Failure modes / limits.** `canonical` is a morphology class, not every valid
centered/no-clipping grid. The validator intentionally rejects off-manifold
shapes.

## D4 — Use a seed-phased period-four schedule

**Choice.** `schedule_profile` cycles through all four profiles, with a
deterministic phase derived from the seed. Every consecutive four sample indices
are complete.

**Original rationale.** The baseline sampled individual pairs without a lesson
coverage invariant.

**Alternatives considered.** Fixed unphased cycle; random profile per pair;
post-hoc rejection of ambiguous lessons only.

**Probe.** For each band, 8 seeds × 12 starts verify every four-index window;
8 seeds × 4 query positions verify every three-demo/query rotation. The shared
census checks 300 production lessons and 1,200 query rotations.

**Why selected.** Completeness is deterministic, while seed phase prevents all
lessons from presenting profiles in one fixed absolute order. Post-hoc rejection
alone can waste draws and conceal a weak sampler.

**Failure modes / limits.** The shared census materializer uses four consecutive
pairs. Other downstream assemblers must preserve that window or invoke
`lesson_identifiable`.

## D5 — Construct orbit geometry instead of rejection-sampling it

**Choice.** Enumerate complete and useful partial orbit groups for a shape/pivot,
then sample one source from each selected distinct orbit.

**Original rationale.** Baseline source did not establish semantic branch
coverage constructively.

**Alternatives considered.** Place random markers and retry until a witness
appears; mutate canonical grids near edges; hand-code a small fixed fixture bank.

**Probe.** `self_check`, independent geometry oracle, 128 draws per band,
600-draw semantic census, and rule smoke.

**Why selected.** Construction makes profile guarantees transparent and avoids
rare-event dependence. Sampling within feasible shapes/pivots/orbits still gives
high instance diversity.

**Failure modes / limits.** Cached orbit enumeration is bounded to the declared
7–14 canvas range. One source per orbit avoids redundant inputs but does not
exercise duplicate sources from the same orbit.

## D6 — Define clipping as per-destination omission

**Choice.** A clipped marker must have 2–3 in-bounds members of its four-position
orbit; in-bounds members are painted and only out-of-bounds destinations are
skipped.

**Original rationale.** Canonical examples contain no clipped orbit, so this
branch was not visible.

**Alternatives considered.** Permit one in-bounds member; discard the entire
orbit; restrict all sources to full orbits.

**Probe.** `edge_clipping` witness, `full_orbits_only` rival, canonical fit check,
60/60 witness/rival disagreement, and explicit clipped/mixed tests.

**Why selected.** At least two in-bounds members create a visible nonidentity
transformation and directly refute the all-or-nothing shortcut.

**Failure modes / limits.** Extremely large offsets with only one surviving cell
are not in the teaching manifold, though the Racket rule can process them.

## D7 — Make off-center evidence behavioral, not nominal

**Choice.** Off-center/mixed construction accepts a scene only when the intended
red-pivot output actually differs from the geometric-center rival.

**Original rationale.** Merely moving the pivot can still produce a symmetric
marker layout whose output coincides with the wrong center.

**Alternatives considered.** Treat `pivot != floor(canvas_center)` as sufficient;
use only odd square canvases.

**Probe.** `_profile_relationships_hold`, independent rival tests, and 60/60
witness/rival disagreement.

**Why selected.** The generated pixels must expose the branch; metadata alone is
not evidence.

**Failure modes / limits.** The chosen geometric-center rival uses integer floor
coordinates on even canvases. Other notions of an even-grid center are not
separately declared rivals.

## D8 — Retain canonical-size support in every difficulty band

**Choice.** Canonical profile always chooses 7×7 or 9×9 and 2–3 markers; other
profiles use band-specific 7–14 dimensions and 2–5 markers.

**Original rationale.** Baseline ranges caused zero exact canonical-profile hits
in medium and hard during the 20-draw floor check.

**Alternatives considered.** Make each difficulty use disjoint sizes; force every
profile to canonical dimensions; opt out of the profile floor.

**Probe.** Final profile floor: easy 6/20, medium 5/20, hard 6/20 exact hits.

**Why selected.** Every band retains an anchor to public morphology while witness
profiles still broaden geometry.

**Failure modes / limits.** Difficulty primarily controls size/marker count, not
a calibrated human or model difficulty score.

## D9 — Reject unknown and invalid overrides before sampling

**Choice.** Validate difficulty, key set, and exact profile token before creating
sampling context.

**Original rationale.** Baseline silently accepted unknown keys and advertised
values outside per-band draw ranges.

**Alternatives considered.** Ignore unknown keys for backward compatibility;
clamp invalid values; rely only on `gen_ctx` errors.

**Probe.** Direct task tests and shared unknown-key override probe.

**Why selected.** Silent fallback makes experiments irreproducible. Immediate
errors preserve the caller's intended intervention semantics.

**Failure modes / limits.** Error strings are informative but not a stable API.

## D10 — Declare executable rivals and witnesses

**Choice.** Publish `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and
`lesson_identifiable`.

**Original rationale.** The baseline had no semantic contract, so the shared
semantic gate could only report `NO_CONTRACT`.

**Alternatives considered.** Describe shortcuts only in notes; test them only in
task-local tests; rely on a generic list of transforms.

**Probe.** Shared semantic gate and source-bound lesson census execute the actual
declarations. All declared canonical shortcuts fit 3/3 public pairs before being
used as competitors.

**Why selected.** Executable declarations are replayable by future agents and
shared tooling. Prose is not enough to reject ambiguous lesson bundles.

**Failure modes / limits.** The rival set is finite and reviewer-chosen. Passing
it does not establish universal identifiability.

## D11 — Keep validation strict to the teaching manifold

**Choice.** `self_check` and `strict_canonical_like` require rectangular ARC
0/1/2 grids, 7–14 dimensions, one red pivot, 2–5 blue sources, one of the four
observable profiles, and a nonidentity output.

**Original rationale.** Baseline validator allowed a broader but internally
inconsistent override surface, including ordinary values that deliberately
removed the pivot or all sources.

**Alternatives considered.** Validate every input accepted by the Racket rule;
permit negative/degenerate fixtures in production; validate only shape/colors.

**Probe.** Malformed/mutated input tests, strict 600/600 measurement, and
canonical acceptance 3/3.

**Why selected.** Training validation should describe the promised distribution,
not the maximum domain of the executor.

**Failure modes / limits.** Lawful Racket inputs outside the teaching manifold are
rejected by design. This distinction is documented in `notes.md`.

## D12 — Synchronize selected authority source without changing behavior

**Choice.** Replace only the nested selected `racket_target.target_code` string
with canonical `program_solution`; retain `raw_code`, which already matched.

**Original rationale.** The extra comment's provenance was unknown. The before
battery showed execution parity but exact active-source divergence.

**Alternatives considered.** Leave diagnostic divergence; modify canonical to
match the selected copy; delete one source field.

**Probe.** Exact source assertions in task tests and final authority-sync report.

**Why selected.** Canonical is the declared authority. Synchronizing the selected
copy removes ambiguity without changing the executable rule.

**Failure modes / limits.** This does not automatically prevent future copies
from drifting; the shared authority gate must continue to run.

## D13 — Add an independent probe and test-first contract

**Choice.** Put independent geometry in `workspace/reference_probe.py` and 49
regressions in `tests/test_generator.py`.

**Original rationale.** No selected task-test directory existed; root frozen
fixtures were not patchable and did not cover the semantic lesson design.

**Alternatives considered.** Test production helpers against themselves; modify
the frozen fixture; rely only on shared battery stages.

**Probe.** Retained red/green TDD logs plus portable `task_tests` stage.

**Why selected.** An oracle that reuses production internals can preserve the
same bug. Portable task tests prove the returned files, public API, and authority
copy travel together.

**Failure modes / limits.** Independent Python geometry could still share a
conceptual mistake with the reviewer; Racket mirror parity and canonical pairs
provide a separate execution check.

## 2026-10-24 reviewer parametric handoff — `review-ea00ed5604a86786`

### Defect → repair

The approved production generator and selected canonical Racket rule were sound,
but the task had no native accepted parametric family. I preserved both unchanged
and added a separate task-local two-setting family under `workspace/parametric/`:

- `completion_scope=all_orbits` returns the exact selected canonical program bytes;
- `completion_scope=most_clipped` computes every source marker's visible rotated
  orbit, selects the unique minimum-visible-count orbit, and completes only it.

The first 30×30 constructor attempt exposed a geometric defect: full orbits around
an off-center pivot cannot by themselves place source markers on all four outer
edges. The repaired stress grammar uses one of eight near-center pivots, lets the
unique count-2 target supply the otherwise unreachable edge, and constructively
chooses count-3/4 distractors to cover the remaining edges and quadrants.

A protected-Racket audit then exposed a second defect: six generated rival
programs had one extra closing parenthesis, so runtime errors could have been
mistaken for hypothesis elimination. A regression test now executes every one of
the ten declared programs and checks it against an independent Python claim.

### Sequential dependency

- **A:** compute the four rotations of every blue source marker around the red
  pivot, filter them to the input bounds, and retain each visible orbit/count.
- **Intermediate:** the unique source marker/orbit with minimum visible count.
- **B:** paint only that selected orbit.
- **Counterfactual:** replace the intermediate with the maximum-visible-count
  (`least_clipped`) marker. On the retained 30×30 qualified query, the correct
  source `[4,1]` has count 2 while the substituted source `[1,28]` has count 4;
  protected Racket produces a different final grid.

### Retained evidence

- Focused suite: 29/29 passed.
- Changed-target task suite: 78/78 passed.
- Authoring audit: six episodes, 230 protected-Racket evaluations, 24
  content-addressed public turns, and 300/300 additional sampler episodes across
  50 seeds (2,300 visible pairs; 150 matched-input comparisons).
- Independent saved-public checker: 24/24 files, zero findings.
- Native qualification: two settings × seeds 0 and 17, three demonstrations,
  four queries, 40 protected-Racket evaluations.
- Source inventory manifest SHA-256:
  `e0bccd2de728ebe58dab256956b25fe388b250231a18b128aae2dc423513a21b`.

The finite rival audit covers the other setting plus least-clipped, first/last,
nearest/farthest, complete-only, clipped-only and first-partial shortcuts. It is
not a universal uniqueness proof. Owner exact-source integration, fresh native
acceptance replay, and any training admission remain pending. The optional peer
targets were left unrun after completing and qualifying MAIN.
