# Working notes: 80f776fb3ce5

## Current reviewed candidate: v2.0.0

Final generator SHA-256: `a30c04fd21088af1a4f89745861eb389b2745ded0ccbe199c9b40774294b10fb`.
Issued v1.3.0 source SHA-256: `755f8a312b5120eba2e6f6b47f8e397160672ea40ad507be8305b76b925ea833`.
The selected Racket authority is unchanged: rule hash `b2e92ad6e68e`, exact
program-text SHA-256 `f0207ca30b93d92086ae237025b35898a0b9d7694b0c16cc293a28d1677b8615`,
normalized-program SHA-256 `b2e92ad6e68e68cbe166833f46c7406360bc66f52b5b82b88e4d5816333e1edc`.
Current records supersede the issued sampler's distribution and override claims;
imported associated notes retain their original timestamps in
`evidence/associated_notes.jsonl`. They are not rewritten as current evidence.

The rule replaces an interior zero with eight exactly when its four cardinal
neighbors are blue one. It reads the original grid, preserves all other cells,
and does not require diagonal zeros. Fixed colors are semantic roles; palette
permutations are not a lawful global symmetry of this task.

## Domains, exact controls and compatibility

`self_check` accepts rectangular 3..30 by 3..30 grids of integer colors 0..9,
excluding booleans, with at least one eligible target. It admits colored clutter,
occupied centers, touching motifs and valid targets next to the border. This
validator domain is wider than the generated distribution. Public rule execution
also accepts target-free grids, but those are deliberately omitted from normal
generation and rejected by this validator: every generated pair must demonstrate
a visible change. No-op negatives occur within changing rich scenes. The retained
degenerate fixtures are diagnostic negatives, not production overrides.

Exactly three override axes remain: `grid_h` and `grid_w`, each integer 6..14,
and `n_patterns`, integer 1..4. These values are legal jointly in every supported
difficulty band (`None`, easy, medium, hard); construction neither enlarges the
canvas nor drops targets. `n_patterns` counts actual eligible centers observed
from pixels. Finite backtracking packs clean plus footprints for compact scenes.
`observe_overrides` exposes exact dimensions and target count.

This is an intentional compatibility change. The issued sampler ignored
`n_patterns`, helpful textures and several claimed axes, accepted misspelled
keys, and used difficulty-specific bounds inconsistent with its published range.
Retired `palette_kind`, `texture`, `palette_size`, `position_bias`,
`n_distinct_colors` and `density` keys now fail explicitly, as do unknown keys,
out-of-range values, non-integer values and unknown difficulty names. `None`
retains the context convention of an unpinned axis. The version bump changes
deterministic layouts; it does not change the authority.

## Default teaching policy and its limits

Sample-index parity supplies period-two profiles: even indices draw canonical
binary scenes, odd indices draw contrast scenes. Unpinned canonical scenes are
square 7..9 with 1..4 clean full pluses. Unpinned contrast scenes are 11..14 in
each dimension and have four eligible targets. Contrast scenes contain a positive
with diagonal clutter, a clean positive where space permits, three-arm partials,
a mixed-color cross, a nonblue cross, an occupied blue-surrounded center and a
diagonal-only pattern. Perpendicular missing-blue arms expose both directional
gap shortcuts. Colored and occupied rims provide coherent contrast motifs.

The default is three demonstrations plus one query. Four consecutive draws have
two contrast examples, so holding out either leaves another contrast example in
the demonstrations. The guarantee is finite-rival identifiability under this
policy. It is not a proof against arbitrary hypotheses. Contrast scenes use
nine spaced 3x3 motif slots in a tiled arrangement. This deliberately supplies
coherent examples but does not measure generalization to arbitrary overlapping,
densely packed or untiled scenes accepted by the validator. Generation's target
ceiling is four: a rival that processes the first four targets would survive this
distribution, and teaching for inputs with more than four targets is unmeasured.
The `cap_three` witness addresses a ceiling of three only. Explicit compact
dimensions can select the clean packing branch even at a contrast index, and
explicit counts below four remove the count-cap witness. Such overrides remain
lawful but do not inherit the default contrast coverage or lesson guarantee.
Materialized lessons and their actual accepted indices must still be checked.

Eight declared canonical-fitting shortcuts are `vertical_pair`, `three_arms`,
`isolated_plus`, `ignore_center`, `nonzero_arms`, `three_blue_nonzero`,
`diagonal_or_cardinal` and `cap_three`. All fit all three labeled canonical pairs.
`horizontal_pair` fits the two canonical training pairs but fails the canonical
test; `identity` fails the changing examples. Those two remain competitors rather
than all-canonical-fitting shortcuts. The namespaces contain 28 declared entries
for ten distinct rival functions. Tests and probes discover the actual declarations.

## Diagonal-support correction and retained counterexamples

The issued sampler's separation policy excluded diagonal clutter at positive
centers, so the isolated-plus rival survived despite the comment claiming that
three demonstrations pinned the intended rule. The repair emits valid crowded
pluses. A later adjustment connected rims to reduce fragmentation, while keeping
the first cluttered positive's diagonal count in 1..4 and retaining a clean plus.
The focused regression `test_connecting_rims_does_not_remove_one_or_two_diagonal_positive_cases`
observes all counts 0, 1, 2, 3 and 4. Restricting positives to only clean or nearly
complete rings would introduce another unsupported diagonal condition; that
restriction was rejected.

`counterexamples/isolated_plus_minimal.json` retains a minimal accepted 3x3 witness
from authoritative corpus index 171. Input: 3 rows x 3 columns. Output: 3 rows x
3 columns. Input rows are `010 / 101 / 011`; selected Racket output rows are
`010 / 181 / 011`; the isolated-plus rival leaves the input unchanged. This witness
is minimal within the enumerated corpus by area, then nonzero count, then
row-major values. It is accepted by the validator but is not an emitted 3x3 sample.

`counterexamples/isolated_plus_generated.json` supplies observed generated support,
extracted from the first final census lesson's second training pair: seed
`900844272`, sample index `1`, easy difficulty, no overrides, contrast profile.
Input: 14 rows x 12 columns. Output: 14 rows x 12 columns. The full input is:

```text
000000000000
000000000000
011101110010
010101010101
011100110010
000000000000
000001000111
101010600141
010001000111
000000000000
000000000000
088801110101
080801010000
088000110101
```

Racket changes precisely centers `(3,2)`, `(3,6)`, `(3,10)` and `(12,6)` (zero-based).
Their nonzero diagonal counts are 4, 3, 0 and 3. The isolated-plus rival changes
only `(3,10)`. Both counterexamples preserve input, Racket output, rival output,
source/rule hashes, exact evidence location and authority provenance.

## Final measured evidence

All counts below bind to the final generator hash above; earlier attempts remain
retained separately and do not count as final-source evidence.

- `WORK/checks/final/result.json`: 12/12 after-battery stages green. Its semantic
  report accepts all 3/3 canonical inputs, records strict support 302/600, verifies
  all 9/9 witness claims, and finds 12/12 production lessons identifiable with
  0/48 ambiguous diagnostic rotations.
- `WORK/checks/required-rotations/result.json`: final-source required-policy gate
  exit 0, 12/12 production lessons identifiable and 0/48 ambiguous rotations;
  strict support 302/600 and all 9/9 witness claims verified. This separately
  supplies required-policy evidence rather than reusing a diagnostic receipt.
- `WORK/checks/task-tests-verified/`: 52 focused tests passed, including portable
  canonical checks, joint support for all 2,592 axis/profile/band draws, exact
  target counts, dynamic shortcut witnesses and all four query positions.
- `WORK/checks/local-contract-verified.json`: all 512 binary neighborhoods plus
  56 compact palette cases labeled by public `Catalog.apply`; 568/568 agree with
  the independent predicate, with zero parity failures. Exactly 24 local inputs
  pass the positive-target validator. This corpus does not establish generated
  support or lesson identifiability. The isolated-plus rival is refuted on 23/568.
- `WORK/checks/lesson-census-verified.json`: 100 lessons in each of easy, medium
  and hard, requested starts 0..99 in each band with the report's hashed seed
  recipe; all 300 materialized, 1,200 pairs, 1,133 unique inputs. Production and
  required query-rotation statuses both `no_ambiguity_found`: zero ambiguous
  lessons or rotations, zero hook warnings, scoring errors or materialization
  errors. These counts cover the declared rivals and the retained sample, not
  undeclared alternatives or every possible seed. Census configuration period
  6 is not the generator's declared schedule period, which remains 2.

The full repository suite completed with 468 passed, one unrelated historical
archival-pair failure for `defba1ab4f90`, and three torch-dependent skips, in
386.38 seconds. `WORK/checks/repository-diagnostic/first-failure.json` records the
reproduced failure and unchanged issued-source hashes. It is not counted as a
passing repository suite or attributed to this task.

No authority change or unresolved task-local failure remains in these checks.
The tiled default schedule, target-count ceiling and exclusion of whole-input
no-ops are explicit distribution choices;
maintainer acceptance is still derived from the complete return and retained
source-bound evidence rather than a changed approval flag.
## Current reviewer considerations

Source SHA-256: `a30c04fd21088af1a4f89745861eb389b2745ded0ccbe199c9b40774294b10fb`.

# Decisions — review-ebf316e09fd688a4

## Scope and authority

The assignment, selected baseline, blind task and two audit targets were kept unchanged. No prior return was used as a substitute for measuring the issued source; the selected task had no unresolved review index to follow. The only repository changes are under `generators/80f776fb3ce5/`. Audit findings are evidence-only. The canonical ledger and Racket authority remain byte-for-byte unchanged, with normalized rule hash `b2e92ad6e68e`.

This is a repair to the input distribution and its contract for the same local rule. It does not introduce a new composed rule, certify transfer, approve the generator, or admit training data. Those decisions remain outside this return.

## R1 — Validator domain and canonical support

**Prior choice:** require multiple full pluses and at least one partial plus. The source stated a goal of demonstrating completion amid distractors; no stronger historical rationale was available. **Problem:** all three canonical inputs fail that validator, even though their outputs are authoritative. The before profile check recorded canonical rejection and no medium/hard exact-profile hits.

**New choice:** accept rectangular integer-color grids, 3–30 rows and columns, with at least one eligible center. Accept lawful occupied centers and other colors as distractors. The separate strict hook characterizes clean binary full-plus scenes; it is not the rule-domain validator. This clean/contrast distinction preserves canonical support while permitting targeted negatives.

**Rejected alternatives:** retaining a mandatory partial plus would keep the canonical contradiction; allowing malformed or empty/no-target grids by default would weaken the positive-example contract. Whole-input no-ops are retained in local diagnostics, but excluded from emitted positive training scenes. The latter is an explicit coverage limitation, not a property of the authority.

## R1 — Exact controls and placement

Keep only dimensions 6–14 and target count 1–4. Reject unknown/retired controls and Python booleans or non-integer values; interpret `None` as no override. Fixed semantic colors 0, 1 and 8 are part of the rule and are not palette-permutation controls. Other nonblue colors may be distractors, while occupied-center contrasts avoid the already-correct output color 8 so that an overwrite rival visibly disagrees.

The original advertised knobs did not all affect inputs, and difficulty-specific size selection disagreed with the declared ranges. A fallback branch could enlarge a requested grid; the retained exploratory sample did not demonstrate that branch occurring, so the claim is limited to the source path. Bounded constructive placement now honors requested shape and eligible-center count; the observer derives both from grid pixels.

The floor of 6 permits four disjoint full-plus placements even at the smallest shape. Rich lessons need enough room for several separated contrasts, so default rich dimensions are 11–14. Explicit compact overrides receive clean exact layouts and remain lawful, but lose the default contrast-teaching guarantee. Making legal small settings randomly fail would contradict the advertised axes; silently growing them was also rejected.

Evidence: 16,020 accepted final battery draws across 178 matrix cases; the task-local regression additionally enumerates all 324 joint settings in four difficulty modes and both schedule profiles at seed 29. These are concrete finite checks; they do not enumerate all random seeds.

## R2 — Teaching schedule and rival scope

Default sample indices alternate canonical-profile and contrast-profile grids, with declared period 2 and minimum three demonstrations. Canonical profiles use square 7/8/9 grids, binary input colors and 1–4 targets at varying positions. Rich profiles contain clean and diagonally cluttered positives, three-arm partials, occupied centers, mixed and wholly wrong-color surrounds, diagonal-only structures, and four true targets.

A default four-pair consecutive window has two rich scenes. With three demonstrations and one held-out query, every rotation leaves at least one rich scene. The test suite checks both cyclic residues and invokes the lesson hook on actual pairs; the 300-lesson census uses production materialization, records accepted sample indices and resampling, and evaluates every pair as the query. This does not authorize arbitrary smaller demonstration counts or override-based lesson assembly.

The finite hypothesis set contains ten distinct rivals. Eight fit all three labeled canonical pairs: vertical pair, three arms, isolated plus, ignored center, nonzero arms, three-blue-plus-nonzero arms, diagonal-or-cardinal surround, and first-three targets. Horizontal pair fits both training examples but fails the labeled canonical test, so it is a lesson competitor rather than a claimed all-canonical shortcut. Identity is also a competitor, not a canonical shortcut.

The lesson checker evaluates both demonstration fit and changed query predictions; surviving a finite demonstration set is not itself scored as an ambiguity when the rival also agrees on the query. The census retains both survival/refutation observations and query effects. We do not describe its 28 namespaced registrations as 28 independent models.

**Rejected alternative:** independent low-probability distractor sampling can miss all important witnesses in a short lesson. Co-locating the contrasts in every rich default scene makes the declared lesson behavior more dependable. **Cost:** the design is visibly tiled and caps generated targets at four; arbitrary clutter and more-than-four-target induction remain unmeasured. A newly invented rival tailored to those restrictions can survive these finite checks.

Final evidence: `checks/lesson-census-verified.json` has 100 lessons per easy/medium/hard band, 300 materialized lessons, no errors, 1,200 overlapping pair occurrences/rotations and 1,133 unique normalized input grids. Its seeds are `sha256('lesson-census:v1:TASK:BAND:INDEX')[:8]` interpreted as uint32, with requested starts 0–99 per band; all exact seeds and accepted indices are stored. The task's period-2 regression complements the shared sampler's period-6 diagnostic metadata. `checks/required-rotations/` makes rotation success a required gate and passes 12 lessons/48 rotations.

## R3 and R4 — Repairing the repair without hiding failures

The first candidate passed the initial 44 tests but its after battery failed fragmentation and semantic witness linkage. Rich scenes had many disconnected cells; `vertical_pair` and `three_blue_nonzero` lacked explicit witness links. We added two regressions that failed, then joined selected motif rims and linked vertical-gap/mixed-arm witnesses. Both failures remain in `checks/after/` and `checks/red-teaching.*`.

The second candidate passed all battery stages, but a further support review found that connecting every positive rim removed examples with exactly one or two diagonal blue cells. A new regression failed with observed support `{0,3,4}` rather than `{0,1,2,3,4}`. The final candidate lets the first cluttered target vary over one through four diagonal cells, keeps a clean target, and uses connected rims elsewhere. This restores the missing support while keeping the final fragmentation gate green.

| Source phase | Generator SHA-256 | Retained result |
| --- | --- | --- |
| Issued 1.3.0 | `755f8a312b5120eba2e6f6b47f8e397160672ea40ad507be8305b76b925ea833` | 5 failed battery stages; initial new regressions: 36 failed, 8 passed |
| First repair | `feafc833bdc2addec9bb3e9ffa84a0e2ba4dff065387fd789b8c658a218f4b42` | 44 tests passed; battery 10 green/2 failed; next 2 regressions failed |
| Second repair | `4078df370f8959e7a9acef7aeaa281f99c6503a4dd51016a5351b52b227de6e0` | 50 tests passed; battery 12 green; subsequent diagonal-support regression failed |
| Final 2.0.0 | `a30c04fd21088af1a4f89745861eb389b2745ded0ccbe199c9b40774294b10fb` | 52 tests passed; battery 12 green; 568 local authority comparisons; 300 lessons/1,200 rotations clear for declared rivals |

Two complete intermediate census reports are gzip-compressed with original length/hash mappings, small JSON pointers at their original paths and a validating restoration helper. The helper replaces only a matching pointer or a missing file, and an isolated round-trip verified both restored originals. All failed stage reports and regressions remain directly retained. None of the intermediate reports is represented as final-source verification.

## Independent checks and reusable tooling

The task-local probe enumerates all 512 binary 3×3 grids and 56 palette/occupied-center extensions. It calls the public authority API and checks an independent center predicate; it also reads current rival declarations dynamically. A single 3×3 grid cannot distinguish a rule capped at three targets, so that rival's local survival is explicitly reported and the generated four-target witness supplies the separate evidence.

Grid validity, authority behavior, generated support and complete-lesson teaching are kept distinct. The smallest isolated-plus counterexample is a validator-accepted 3×3 grid but is not an emitted whole grid; the returned larger example is taken from an actual final-source census lesson. No local enumeration claim is inflated into arbitrary-grid or universal-rival coverage.

Portable task tests initially failed to start because the staged runner disables the Python user site with `-E -s`, where pytest happened to be installed. We created an environment outside the source tree and made the already-installed pure-Python pytest dependencies visible there. The isolated import receipt and failing first stage are retained. No shared runtime, test fixture or packaging code was changed.

The broader repository run finished with one unrelated archival failure and three missing-PyTorch skips. That run was not snapshotted and overlapped the final selected-task iteration, so it provides repository context rather than final-source certification. A focused failure reproduction identifies an unchanged task and unchanged test, both matching the issued manifest. Repairing that separate historical expectation or installing a large optional dependency is outside this assigned delta; its deeper cause remains unresolved.

## Audit and solve decisions

A1 and A2 are reproduced teaching-coverage findings with actual Racket query outputs. A1 also has three Racket-labeled generated demonstrations. A2's 144-case support probe uses independent Python plus the generator's mirror, so only its retained U-corridor application is described as a Racket comparison. Neither source was patched, and an accepted hand-built/canonical counterexample is not claimed to be emitted when the generator excludes it.

The blind solve was completed before opening repair sources. The final solve was prepared only after generator bytes were frozen, and earlier exposure is honestly declared `yes`. During both episodes the visible challenge was the evidence available to the solver; no reference or private query labels were consulted. Both genuine first solution revisions passed their three visible pairs; no accidental failure was invented to create a negative example. Masked correctness remains unknown.

## Final handoff policy

The exact packaged patch is replayed against a fresh extraction, with an isolated Git root at its `WORK/` directory. Focused regressions are rerun there, and the final solve's generator binding is compared with those bytes. The final archive may add report/evidence updates after replay, but its source patch must be byte-identical to the replayed patch. `checks/replay/receipt.json` records the successful apply/check, independent 52-test pass and import provenance. `checks/handoff-source-bindings.json` confirms all final targeted evidence and the final solve use the same source.
