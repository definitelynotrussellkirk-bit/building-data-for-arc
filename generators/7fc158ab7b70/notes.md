<!-- native-parametric-current:start -->
## Current native parametric decision

The separate six-setting `workspace/parametric/` proposal now has a thin native
adapter, exact-canonical default resource and promotion contract. The production
`generator.py` remains SHA-256
`9070d806a5720ecc39eae06c4294c338f5a7afb564e0c89ad36af898fbd6369f`;
the selected canonical program remains
`79bfc5d2e127c997c2f45f184b16a5411dcc8ae746a8fae7cf6c34ad7c42a4de`.

Independent requests support two through six demos and one through four queries.
Constructive separated-pair and L-triomino demos distinguish both count bases,
all axes and the tested component/size shortcuts. Matched inputs span sizes 3–5;
six-color corner/interior queries reach 30×30 under both counting bases. The
original grammar and canonical production approval are unchanged.

The setting-named public-directory defect is corrected. Public paths hash only
visible serialized bytes; solver turns reveal one input without future-query or
count metadata. A real-Racket writer regression verifies identical first turns
for one/four-query calls and invariance to private changes. The original writer,
README and inventory remain under `evidence/public-id-correction/original/`.
The source-bound correction is reviewer-reported, not an owner rerun.

Current reviewer checks: 111 task tests pass; native qualification covers 12 jobs
(six settings, seeds 0/17, three demos/four queries) and 84 labels via 264 protected
Racket evaluations. The two-demo self-audit refutes 21 finite rivals in every
one of 12 episodes, with 258 protected evaluations and no runtime errors. Its old
sampler probe found no held-out counterexample in seeds 0/17; no broader claim
is made. The native causal witness changes only canonical `nz` from 4 to 2 and
replays the resulting 16×16 versus 8×8 output difference.

Current inventory: `workspace/parametric/evidence/manifest.json`. Return checks
are under `checks/7fc158ab7b70/`, including native qualification/execution,
`self-audit-final/audit.json`, and `causal/witness.json` with replay. These finite
results do not establish universal learnability or measured training benefit.
Next action: integrate this proposal, then perform native qualification and
fresh owner acceptance on the exact live bytes. No variant acceptance, training
activation, or resolution of unrelated historical audits is claimed here.
<!-- native-parametric-current:end -->

# Current working notes: 7fc158ab7b70

## Intended rule and retained domain

Original ARC family: training `ac0a08a4`. Count all nonzero **cells**, then
replicate every input cell into a square block with that side length. Zero cells
are replicated too. The canonical Racket authority remains `d959c287782b`.

Inputs remain square grids of side 3–5 with 2–6 nonzero cells, integer colors
0–9, and output side at most 30. The existing validator deliberately permits
monochrome inputs only as two spatially separated cells. Exact public controls
remain `grid_n`, `n_cells`, `unique_colors`, and `anchor_origin`, subject to the
existing difficulty/output limits. These domain choices were inherited; this
review adds no new spatial or palette restriction.

The retained nine-step size schedules decouple grid size from the three-step
palette schedule. Every rolling nine-sample window covers all six
`(grid_n, unique_colors)` pairs. The repeated-color teaching schedule distinguishes
cell counting from distinct-color counting. This is a pairwise support guarantee,
not unrestricted Cartesian coverage or a proof against all plausible rules.

## Current repair: strict seed types

Review `review-cd852f8d87a7ba3f` starts from source
`82870834ac6e72252cbf4764dcd3f78bd65d263c9e025dc789717cca8218823b`.
The baseline battery completed with 11 of 12 stages passing; defect lint found
that boolean, float and string seeds were accepted despite the integer contract.
`generate` now checks `type(seed) is int` before deriving its RNG seed. Actual
integers, including negative and large values, retain their previous behavior.
The minimal boolean counterexample is `counterexamples/non_integer_seed.json`;
`tests/test_seed_contract.py` covers invalid types and valid deterministic calls.

The resulting generator SHA-256 is
`9070d806a5720ecc39eae06c4294c338f5a7afb564e0c89ad36af898fbd6369f`.
`VERSION` stays `2.1.0` because it contributes to the RNG salt: incrementing it
would resample every valid call for an unrelated validation repair. Exact source
hashes distinguish the versions of the code. The final twelve-stage battery
passes. Both canonical and archival reference bytes are unchanged.

## Proposed aggregate-count replication variants

`workspace/parametric/scaling.py` is a separate **proposed prototype**. It exposes
`count_basis = cells | colors` and `scale_axes = both | rows | columns`, selected
once per episode. The canonical default is `cells + both`; `--seedchoose` uses
a deterministic rule-selection stream separate from input generation. The
aggregate-count-then-replicate reasoning remains invariant across all settings.

All six settings retain the same conservative input domain. Three contrastive
demonstrations distinguish the six declared settings; four distinct queries are
the default and are independently configurable. Each setting emits its matching
Racket expression and derives labels through the included protected bridge.
The Python mirror checks parity. Public files contain only demonstration pairs
and query inputs; settings, programs, reference metadata and answers are private.

The retained seed-17 suite has 18 demonstrations and 24 queries across six
episodes. Every episode has seven distinct inputs, a singleton demonstration
survivor and no ambiguous query within the six-setting family. Default parity is
checked against the unchanged canonical Racket on all seven shared inputs.
This is bounded prototype evidence, not production approval, universal
identifiability or training admission. Exact commands and limits are in the
prototype README; focused tests are in `tests/test_parametric_scaling.py`.

## Prior findings and remaining limits

The earlier audit `review-2b9742c54a64d33c:v0001` concerned source
`4401f950f141d3f74df33c5664b285c19cbb9b638f1c835ba867a1cd14c4cad8`.
Its distinct-color rival remains a useful canonical-fitting hypothesis. On the
current source, repeated-color overrides and ordinary repeated-color draws are
accepted and refute it. The inherited review index still records that historical
finding as needing triage; this review does not rewrite its administrative status.
The prior accepted return `review-3698d4252a1cb7a7:v0001` was a source-history
lead, not a substitute for this review's measurements.

The current repair preserves the existing distribution. Output bounds prevent
large inputs in this retained domain. Finite declared-rival and prototype checks
do not establish unique induction against arbitrary alternative programs.
The two new findings-only audits concern other tasks and are retained in this
return's AUDIT.md, without modifying those generators.


## Current proposed prototype public identifiers

The canonical seed repair is accepted independently of this proposed prototype. Its writer exposes setting.name in public directory names. Preserve exact reviewer source and evidence; an external follow-up must use visible-content-only public paths and verify the corrected Racket writer with a focused privacy regression. Pending source-bound work: `generators/7fc158ab7b70/evidence/parametric-public-identifiers-pending-cd852f8d87a7ba3f/manifest.json`. Owner execution was not performed, and the prototype remains unapproved. Earlier main audits are not cleared by this seed-only acceptance.
## Current reviewer considerations

Source SHA-256: `9070d806a5720ecc39eae06c4294c338f5a7afb564e0c89ad36af898fbd6369f`.

# Decisions and evidence

## D1 — Keep the recorded task and original authority

Assignment `review-cd852f8d87a7ba3f` selected `7fc158ab7b70`, original family
training `ac0a08a4`, through the original-family parametric queue. The single
committed seed and immutable baseline were preserved through recovery. The
canonical rule counts nonzero cells, then replicates every input cell in both
dimensions by that count. The current source and canonical examples agree.

Prior accepted return `review-3698d4252a1cb7a7:v0001` and older findings-only
audit `review-2b9742c54a64d33c:v0001` were source-history leads. Their claims were
not treated as fresh measurements. The older audit's repeated-color override
now validates and separates the color-count rival, as recorded in
`checks/canonical-shortcut/report.json` and its supported Racket receipt.
Its review-index status remains untouched.

## D2 — Retain the existing distribution; repair the measured seed contract

The before battery completed all twelve stages: eleven passed, while defect lint
found fifteen warnings because boolean, float and string seeds were accepted.
The production change is an exact integer-type guard at the start of `generate`.
It raises `TypeError` before deriving the RNG seed. This prevents invalid seed
types from silently becoming a different reproducible sampling stream.

The regression was run against unmodified behavior: 24 invalid-type cases failed
and 12 valid-integer cases passed. After the two-line repair, those 36 cases and
the thirteen existing tests passed. The separate prototype adds twelve tests;
the required portable task-test stage ultimately passed all 61, with no errors,
failures or skips. Initial environment and disk failures are retained separately.
See `checks/seed-contract-red.log`, `checks/seed-contract-green.log`,
`checks/task-tests-console.log` and `checks/task-tests-retry/result.json`.

The baseline and final generator hashes are respectively
`82870834ac6e72252cbf4764dcd3f78bd65d263c9e025dc789717cca8218823b` and
`9070d806a5720ecc39eae06c4294c338f5a7afb564e0c89ad36af898fbd6369f`.
`VERSION` remains `2.1.0` because its text contributes to the RNG salt. Raising it
would change every valid integer-seed draw for an unrelated validation repair.
Source hashes provide exact revision identity. A root comparison retained 300
unchanged valid calls; an independent reviewer checked another stated 600-case
matrix, also with no differences. These are two finite probes, not a claim of
900 distinct inputs. The unchanged execution path for actual integers explains
the compatibility; the probes corroborate it.

Rejected alternatives were coercing invalid types and replacing the seed salt.
Coercion would conceal caller mistakes; resalting would introduce irrelevant
distribution changes. No canonical or archival rule text was edited.

## D3 — Preserve the conservative input choices and their limits

Square inputs remain side 3–5, with 2–6 nonzero cells and output side at most 30.
Colors remain integers 0–9. Existing exact controls and difficulty compatibility
remain unchanged. Monochrome inputs retain the inherited constraint of exactly
two spatially separated cells. The exact original reason for every such domain
restriction is not recorded; this review does not infer a general ARC law from it.

The inherited nine-step size schedule breaks an earlier size/palette correlation.
Its focused tests cover all cyclic starts for the six `(grid_n, unique_colors)`
pairs. The three-step palette schedule retains repeated-color teaching examples.
Removing these restrictions or randomizing their joint schedule was unnecessary
to fix the measured seed defect and would need fresh domain evidence.

The after battery passes all twelve stages. Strict-profile checks accepted
600/600 draws; exact canonical-profile support was easy 5/20, medium 6/20 and
hard 9/20, pooled 20/60. Envelope support was also 20/60. Live rule smoke applied
120 inputs, with 120 mirror comparisons and zero mismatches or rule crashes.
This establishes the stated finite coverage, not corpus-wide validity.

## D4 — Add two parameters that change the executed rule

The separate proposed prototype varies `count_basis` over `cells | colors` and
`scale_axes` over `both | rows | columns`. The original setting is `cells + both`.
All six settings preserve the causal structure: compute an input aggregate,
then use it as a replication factor. Color counting is a meaningful nearby
rule already exposed by the canonical-fitting rival. Axis selection changes
the spatial replication without introducing unrelated object logic.

Pure changes to palette, positions or size would not satisfy the rule-variant
request. Arbitrary rotations, background changes or extra composed operations
were rejected because they would obscure the original reasoning. All six
settings share the conservative original input domain, avoiding a confound
between the selected rule and the allowed input dimensions. Output limits then
hold without setting-specific sampling restrictions.

Explicit parameter values or `--seedchoose` resolve one setting per episode.
The setting is never resampled per pair. Rule selection and input generation
use separate deterministic streams. The default preserves canonical execution;
the prototype does not modify production interfaces or approval metadata.

## D5 — Teach the fixed rule before testing four queries

The three demonstration profiles have nonzero-cell/distinct-color counts
`(2,1)`, `(4,2)` and `(3,3)`. The first separates the count bases but leaves
color-count axis choices tied because their scale factor is one. The second
resolves that ambiguity. The third shows a lawful case where the count bases
coincide. The test suite explicitly checks the first-demo ambiguity and the
complete context's singleton survivor.

`identify_demonstrations` has no query argument. Its fixed survivor set is then
used to assess every query. Queries are distinct from each other and all demos;
the bounded sampler fails explicitly rather than duplicating a pair or silently
returning fewer examples. `--train` accepts 3–20, `--test` 1–100, with defaults
3 and 4. Large requested counts were not exhaustively tested across all seeds.

The retained seed-17 suite has six complete episodes, eighteen demonstrations
and twenty-four queries. Each episode has seven unique inputs and one surviving
setting; there are no ambiguous queries within the six declared alternatives.
All labels come from their instantiated Racket expressions. Forty-nine distinct
executions cover 42 setting/input combinations and seven unchanged canonical
reference applications; caching reuses only those executed results. Default
canonical parity holds on all seven shared inputs. Cell-count variants reach
an output side of 30; color-count variants reach 15 in this suite.

Public JSON includes only demonstration input/output pairs and query inputs.
Private JSON retains settings, programs, query outputs and rival receipts.
See `checks/parametric/validation.json` and the source-bound suite manifest.
This is a proposed prototype with finite evidence, not training admission.

## D6 — Keep production, rotation and multi-query evidence separate

The fresh source-bound census materialized 100 lessons per difficulty band,
300 production lessons in total, with one query each. All 1,200 pairs were
labeled through the selected canonical Racket rule. There were 1,189 unique
normalized inputs, no materialization/scoring errors and no declared-rival
ambiguities. Holding out each materialized pair once produced 1,200 rotations,
again without ambiguity or hook warnings. Rotations reuse those bundles;
they do not enumerate every possible schedule window or all plausible rules.

The separate production command requested four queries at seed 17 and obtained
three demos plus four queries, all seven inputs distinct. Every query passed
the lesson hook after demonstrations refuted the declared color-count rival.
The first command correctly refused changed, unapproved source. It was repeated
with the documented `--allow-unapproved` research flag; the result remains
explicitly unapproved. No approval hash was refreshed to make the command pass.

## D7 — Record audits and infrastructure proposals without widening the patch

The two fixed audit targets are findings-only: `914cf1c42d85` sometimes omits a
required size-four component, and `47be86674731` permits a concentration shortcut
with a validator-accepted separating query. Both have saved source-bound
counterexamples and exact canonical Racket apply receipts. Their source is
unchanged; complete denominators and limits are in `AUDIT.md`.

Actual extraction and portable-test-copy ENOSPC failures justified targeted
recovery. The original ZIP's manifest sources were fully hash-verified; a sparse
local checkout is not described as a passing stock full-local verify. The
recovery helper, native early-seed-journal patch and tests remain separate
proposals under `checks/tooling/`. They are not smuggled into the allowed task
delta. Final packaging and fresh replay evidence are summarized in `REVIEW.md`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7fc158ab7b70/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
