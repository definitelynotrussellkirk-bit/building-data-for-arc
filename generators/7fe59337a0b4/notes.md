# Working notes: 7fe59337a0b4

## Native parametric build — reviewer ready

Built a separate `links=none|first_hit` family. `none` preserves the exact
canonical program. `first_hit` renders the four rotated copies first, then
traces four marker-colored rays through that rendered grid, stopping before
the first occupied cell; a ray with no hit paints nothing. Thus the stopping
positions depend on the transformed motif rather than its original location.

Implementation scope: `workspace/parametric/{native_family,sampler,adapter,audit}.py`,
its canonical resource, native promotion/inventory, and focused task-local tests.
Use three constructive demonstrations (support 3–6), four independent novel
queries (support 1–4), and matched input streams across settings/counts. Extend
only this prototype to 9–30 square canvases and larger connected asymmetric
motifs; require all four placements in bounds, mutually disjoint, and clear
of the marker. Production's 9–15 / small-motif / eight-demo contract is unchanged.

The first build completed focused tests, protected competing-rule self-review,
teaching repairs, source freeze, native qualification, causal replay and public
projection checks before work began on the second assigned build.
No owner acceptance or training admission is implied by reviewer qualification.

Final reviewer checks: 85 focused tests passed; 68/68 finite rival comparisons
were demo-refuted in protected Racket on seeds 0 and 17 (123 unique executions,
including 3 canonical pairs). The maximum-seed six-demo/four-query boundary probe
checked 20 labels. Native qualification passed 4 jobs / 40 executions; 16 one-query
public views verified, with leaked-answer/orphan/missing-view mutations rejected.
The causal witness independently replayed two original-input stop-cell
counterfactuals, changing 16 and 10 cells.

Self-review found and repaired a real gap: original seed 17 sources N/NE/E
allowed a below-source-only reversal to fit all three demonstrations under both settings
and change 12 cells on the 13×13 query. The full failing lesson/source remains
in checks/7fe59337a0b4/self-review-below-source-v1.json and its source folder.
The revised N / SE+W-or-SW+E schedule teaches all four open half-planes
without adding demos; the retained four query inputs are unchanged. Final
evidence is audit-r2, native-tests-final, qualification, causal and preview.
Earlier red tests, initial source-center revision and audit-r1 are superseded.
The first self-review probe invocation failed on a relative runtime path
before label execution; the corrected successful receipt is retained too.

This is a separate qualified prototype, still pending owner acceptance.
Production source 3b9c9ef989d5688979c834e636902d40e60622b7e19110d82eed60227c15c975
and canonical e5504f0fdce0 remain unchanged; no active production finding
was silently cleared. Full eight-sector identifiability and universal rule
uniqueness are not claimed for the three-demo prototype; no training admission.

## Current intended rule

Crop the sole nonzero, non-9 motif. On a fresh black canvas, place the original
immediately north of the unique color-9 marker, then place 90°, 180°, and 270°
clockwise rotations east, south, and west. Retain the marker and motif color.
The selected Racket authority remains unchanged at `RULE_HASH=e5504f0fdce0`.

## Current distribution decision (version 3.0.0)

The accepted `local-random-2539176eb686` repair used four diagonal source
profiles. A larger census found no label ambiguity but showed that production
never emitted cardinal source alignment, while two canonical inputs are
north-aligned. This reverses the prior four-slot decision.

Use an eight-slot exact schedule covering all compass sectors in alternating
cardinal/diagonal order: `N, SE, E, NW, S, NE, W, SW`. North and northwest use
the canonical oriented L; the remaining six use the existing asymmetric shape
catalog. Lessons require eight demonstrations. Every one-pair holdout from nine
consecutive samples retains at least seven profiles and both sector classes.

## Evidence

- Final generator SHA-256:
  `3b9c9ef989d5688979c834e636902d40e60622b7e19110d82eed60227c15c975`.
- Official after battery: 12/12 green.
- Rule smoke: 120/120, zero Racket/mirror mismatches.
- Exact overrides: 18,000/18,000 accepted, zero findings.
- Semantic gate: 12/12 witnesses/rival claims, 12/12 lessons, 0/108 ambiguous
  query rotations.
- Large census: 300 lessons, 2,700 pairs, 2,224 unique inputs, zero production
  or rotation ambiguities/warnings.
- Portable focused tests: 7/7 passed.

The source-bound `diagonal_source_only` counterexample is retained under
`counterexamples/` and rebuilt by `workspace/build_diagonal_only_counterexample.py`.

## Known limits and open findings

Identifiability is established only against the four declared executable
rivals and the tested schedules/samples, not all conceivable hypotheses.
Absolute directions and colors 0/9 are semantic, so arbitrary D4 or palette
augmentation is unsafe without relabeling. Recipient-side independent monitor
replay and promotion remain external to this review.
## Current reviewer considerations

Source SHA-256: `3b9c9ef989d5688979c834e636902d40e60622b7e19110d82eed60227c15c975`.

# Decisions — `7fe59337a0b4`

## D1 — Keep the canonical rule unchanged

**Prior choice:** the accepted repair `local-random-2539176eb686` bound the
generator to the selected Racket authority and supplied a Python mirror.

**Probe:** the before battery passed canonical acceptance, authority sync, and
120 rule-smoke applications with zero mirror mismatches. The observed problem
was absent source topology, not wrong outputs.

**Decision:** retain the Racket code and `RULE_HASH=e5504f0fdce0` exactly.

**Rejected alternative:** rewriting the Racket for style or to accommodate a
new distribution. That would add authority risk without addressing the actual
coverage defect.

## D2 — Replace four diagonal profiles with all eight compass sectors

**Prior choice reversed:** the earlier curriculum used one canonical northwest
L and three varied motifs in NE/SW/SE. It guaranteed all four diagonal quadrants
in four demonstrations.

**New evidence:** `checks/source-sector-coverage.json` records a 3,000-input
probe (1,000 per band) with exactly 0 cardinal sources in v2.0.0 and an even
1,500 cardinal / 1,500 diagonal split in v3.0.0. Two of three canonical inputs are north-aligned. The retained
`diagonal_source_only` rival therefore fit the old production support while
failing those canonical inputs.

**Decision:** use eight exact profiles ordered `N, SE, E, NW, S, NE, W, SW`.
The alternating order ensures every one-pair holdout from a nine-pair bundle
keeps both cardinal and diagonal evidence.

**Rejected alternatives:**

- Randomly choose cardinal or diagonal placement inside four broad profiles.
  This weakens exact observability and does not guarantee lesson-level coverage.
- Keep four demonstrations and sample only four of eight sectors. This leaves a
  deterministic shortcut available in some complete lessons.
- Add cardinal examples without a schedule. Frequency is not a guarantee that a
  particular exported lesson contains the needed witness.

**Cost:** lessons increase from four to eight demonstrations. For this tiny ARC
object task, stronger support was preferred over a shorter but conditionally
ambiguous curriculum.

## D3 — Preserve the strict canonical floor with two anchors

Eight sector profiles would reduce a single anchor to 12.5%, below the declared
20% floor. The north and northwest profiles therefore both use the canonical
oriented three-cell L. The other six use the existing 13-shape asymmetric
catalog. The final semantic census measured 137/600 strict hits (22.8%) and the
profile floor found support in all three bands.

A lower `MIN_STRICT_FRAC` was rejected because it would hide the regression
rather than preserve canonical resemblance.

## D4 — Make lesson validation rotation-safe but still structural

**Prior behavior:** `lesson_identifiable` required all exact profiles. This was
valid only for an ordered four-demo lesson; holding out one unique profile
caused 900 warnings in the before rotation census.

**Decision:** require eight demonstrations, at least seven distinct profiles,
at least one cardinal and one diagonal sector, valid labels, and refutation of
every declared competitor. Nine consecutive scheduled pairs contain one
repeated profile, so every single-query holdout satisfies this contract.

Dropping all profile/sector coverage checks and relying only on rivals was
rejected; it would make the hook blind to accidental schedule collapse.

## D5 — Add a source-bound data-shortcut rival and counterexample

The executable `diagonal_source_only` competitor agrees with the intended rule
on diagonal sources and emits four unrotated copies for cardinal sources. It is
not claimed to be the only plausible wrong rule; it is a minimal reproduction
of the measured support gap.

The JSON counterexample records the generator hash, exact call, input,
canonical mirror output, and rival output. A focused test rebuilds it and checks
that source bytes still match the recorded hash.

## D6 — Test contracts at the portable boundary

Seven task-local tests cover:

1. all eight source sectors in every sliding schedule window;
2. exact canonical-north generation and observation;
3. all profile/size boundary combinations;
4. lesson-level refutation of the diagonal-only rival;
5. every query holdout for 16 cyclic starts in all three bands;
6. complete witness-to-rival metadata;
7. retained counterexample replay and source binding.

They were run through the official portable `task_tests` stage rather than only
from the source tree.

## Known limits

- Finite rivals and sampled lessons do not prove universal identifiability.
- Direction is absolute; D4 augmentation changes the rule unless labels are
  regenerated under transformed semantics.
- Colors 0 and 9 have fixed background/marker roles.
- The candidate remains subject to recipient-side independent monitor replay
  before promotion.
