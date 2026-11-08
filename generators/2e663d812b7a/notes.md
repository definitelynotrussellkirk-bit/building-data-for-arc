# Current notes: 2e663d812b7a, version 1.3.0

Review `review-b33217a1534467e5`; original family `training:9356391f`.
Selected generator SHA-256:
`c14518d0be325525090968de13d9598d195cf38a7c5f8732a0d87925cc80ca39`.
Canonical `RULE_HASH=f67ec6a58878` and all reference/approval records are unchanged.

## Intended transformation

Row 0 is a positional color key; row 1 is the full gray separator (color 5).
There is exactly one seed below the separator, matching key[0], on a zero
background. Paint the lower canvas by Chebyshev distance from that seed using
the original key. Internal zeros are empty rings; repeated colors keep their
positions. A nonzero header entry becomes gray when its complete ring does not
fit within the lower canvas. An overflowing zero remains zero. Body painting
uses the original key, not the marked header. Racket remains the label authority.

## Input and API contract

Height and width are integers 9..30. Key length is 1..min(10,width), with nonzero
endpoints, 0..8 internal zeros, and 1..6 distinct nonzero key colors excluding
separator color 5. Exact controls are `grid_h`, `grid_w`, `key_len`,
`palette_size`, `zero_rings`, `seed_r` (2..height-1), and `seed_c` (0..width-1).
Unpinned choices adapt to feasible pinned controls. Infeasible pinned tuples
raise `ValueError` identifying incompatible axes; no pinned value is clamped.
These are generation limits, not a claim that every other executable input is
conceptually invalid.

`seed` must have exact Python type `int`; signed seeds are supported.
`sample_index` must have exact type `int` and be nonnegative. `difficulty` is
`None` or an exact string in `easy`, `medium`, `hard`. Booleans, floats, numeric
strings and unknown difficulty names raise `ValueError`. This repairs 48
reproduced permissive-scalar cases in v1.2.1. Override scalars retain the existing
strict contract; `None` means unpinned.

Earlier ineffective selectors remain retired: `palette_kind`, `texture`,
`anchor_corner`, and `asymmetry_force`; `seed_position` remains replaced by exact
row/column controls. Lawful `key_len=1` requests remain admitted with
`ALLOW_IDENTITY_OUTPUT=True`, while default keys have length at least two.

## Distribution and teaching schedule

The alternating `rich_top`/`varied` phase is retained. The declared combined
size/teaching period is now 10, using `(seed + sample_index) % 10`:

| Slots | Default geometry | Share of a complete cycle |
|---|---|---:|
| 0, 2, 4 | Rich 16x16 | 30% |
| 6, 8 | Rich 30x30 | 20% |
| 1, 3, 5, 7 | Varied rectangle with at least one side 21..30 | 40% |
| 9 | Varied 9..18 | 10% |

Rich inputs retain a positional zero, a repeated key color, four nonzero colors,
key length 6..8, and a seed near the top boundary. They distinguish all ten
declared rivals, including four that fit every stored canonical pair. Varied
inputs keep complete/edge/free placement, variable palettes/gaps, and the full
range of exact controls. Some large varied inputs use keys of length 9..10 and
seed coordinates beyond 18; this extends actual rule use beyond blank padding.
Overrides may change teaching properties, so schedule claims concern defaults.

Reversal from v1.2.1: the 9..18 ceiling and exclusively 16x16 rich phase kept
runtime bounded and canonical-profile support, but excluded larger applications
of the same rule. The new mixture retains 16x16 anchors while adding 30x30 and
large rectangles. At seed 735, indices 0..99 in each band, all 300 inputs are
valid; each band has 30 exact 16x16, 20 exact 30x30, 60 with a side above 20,
and 47 rectangles. The strict profile gate still has 17/60 exact and envelope
hits (easy 6, medium 6, hard 5).

The current measured lesson policy is **three demonstrations plus one query**,
with production order preserved. The source-bound random census checks 300
lessons, 1,200 unique inputs and all 1,200 held-out rotations with no declared
rival ambiguity. The fixed-seed schedule census checks every start residue in
all three bands: 30 overlapping lessons, 120 rotations, 21 unique inputs.
This replaces the older review's four-demo/five-pair measurement; its counts
are not evidence for this source. Neither finite census establishes universal
identifiability, arbitrary override support, or model-training gains.

## Separate proposed parameter

`workspace/parametric/prototype.py` implements episode-level `ring_metric`:
canonical `chebyshev` or proposed `manhattan`. The default Racket text is
byte-identical to the canonical program; the other setting changes only the
body distance expression. Three demonstrations and a larger query use one
fixed setting per episode. The prototype has its own 1..20 key-length domain,
explicitly separate from this generator's 1..10 domain. Public exports contain
demonstrations and unlabeled query inputs; private authoring records retain
labels, rival checks, actual Racket receipts and hashes. Nonempty output
directories are refused before writing, so reruns cannot certify stale files.
This is a tested prototype, not an approved variant or selected production rule.

## Evidence and open issue

The official return retains before/after batteries, red/green regressions,
portable task tests, all 38 final Racket boundary checks, full lesson reports,
both solve records, prototype evidence and two independent audits. Complete
commands and evidence paths are in its `RESULTS.json` and `REVIEW.md`.

One shared-tool blocker remains: stock `shared/tools/generator_defect_lint.py`
samples `generate(sd, sd)`, which always reaches the rich phase here. Its four
after warnings (three axis-span and one persistent-marker mismatch) come from
that aliased population. The return includes a separate sampling patch and
reproducer under `checks/linter-proposal/`; it does not silently edit shared
source or claim the stock battery passed. The initially missing schedule receipt
was supplied to a successful final semantic-gate rerun. An inode-exhausted census
attempt is retained separately from the completed 300-lesson retry.

No training-admission or Qwen3.5-9B performance claim is made.

## Current owner source and evidence limits

Accepted1.3.0 strict scalars and9..30 geometry with canonical anchors. Canonical Racket unchanged. Reviewer180 tests plus9 subtests,38 Racket boundary cases and300 default input checks pass. Production3-demo/1-query census300 lessons/1200 rotations and1200 unique inputs clean against declared rivals;period10 all starts at seed0 in3 bands30 overlapping lessons/120 rotations/21 unique inputs. Stock after battery10/12;separate final semantic gate passes with schedule receipt,leaving four aliased-sampling defect-lint warnings unresolved. Separate optional sampler patch has six reported regressions and candidate strict lint zero findings;not installed into shared tool. ring_metric chebyshev/manhattan prototype has47 Racket executions and11 tests;bounded seed/settings only. Owner corrected ordered public filenames and retained actual Racket export from naming tests. No stock-gate waiver,production parameter API,variant approval,training admission or owner repair battery rerun.
## Current reviewer considerations

Source SHA-256: `c14518d0be325525090968de13d9598d195cf38a7c5f8732a0d87925cc80ca39`.

# Decisions for review-b33217a1534467e5

Task `2e663d812b7a`, original family `training:9356391f`, v1.2.1 → v1.3.0.
Final selected generator SHA-256:
`c14518d0be325525090968de13d9598d195cf38a7c5f8732a0d87925cc80ca39`.
Findings R1/R2/P1/U1/U2/F1 correspond to the table in `REVIEW.md`.

## Preserve canonical authority and the original reasoning pattern

The inherited v1.2.1 notes describe the earlier repair of the separator, zero
and repeated key entries, exact controls, and identity-output integration. Those
notes were read as historical rationale, not treated as current-source test
results. This review independently ran a before battery. The canonical ledger,
reference sources, root frozen fixture, and training-approval metadata remain
unchanged. `RULE_HASH` stays `f67ec6a58878`.

The task's relationships are positional key → distance from seed → ring color,
plus lower-canvas boundary → header marking. A Python semantic model is useful
as an independent comparison, but does not replace actual Racket labeling.
`checks/size-boundary-final.json` retains exact inputs and 38 actual executions;
the full production and schedule censuses also use the selected Racket rule.

The supplied packet prioritizes a small parametric extension. That work was
developed in parallel as a separate authoring prototype while canonical defects
were reproduced and repaired; it was never selected as the production labeler.

## R1: reject invalid public scalars instead of coercing them

The before linter reports 48 accepted invalid-scalar cases. The focused red run
also fails on booleans, floats, numeric strings, negative sample indices, and
unknown or nonstring difficulty values. The old behavior relied on permissive
downstream conversions; no documented rationale justified accepting these calls.

The new policy accepts exact integer seeds (including negative integers), exact
nonnegative integer indices, and `None` or the three named difficulty strings.
It raises `ValueError` before generation on anything else. Coercion was rejected
because it silently merges distinct requests and masks caller mistakes. Rejecting
negative seeds was also rejected: they are useful deterministic entropy and have
no sample-index meaning. Existing override validation and structured joint-axis
rejections remain in force.

Evidence: `checks/focused/red.log` has 59 failures and two passes: 48 scalar
failures plus 11 missing larger-grid behaviors. The first pre-red attempt lacked
pytest; `checks/focused/before.log` is retained as an infrastructure failure,
not counted as red evidence. After repair, the 108 inherited and 61 new tests
pass in `checks/focused/green.log`. Representative invalid calls are retained
under the task's `counterexamples/review-b33217a1534467e5.json`.

## R2: extend useful geometry while retaining canonical support

The previous 9..18 dimension range was justified in inherited notes as bounded
runtime with canonical 16x16 support. It excluded larger applications of the same
ring and clipping relationships. The chosen new maximum is 30 for both dimensions;
seed coordinates extend with the actual canvas. Exact key-length, palette and
zero controls retain their previous limits. Unpinned choices adapt to explicitly
requested large coordinates or key widths; incompatible pinned tuples fail.

The default ten-slot mixture is deliberate:

| Slots | Phase / geometry | Purpose |
|---|---|---|
| 0, 2, 4 | Rich, 16x16 | Preserve canonical-profile anchors and explicit rival witnesses |
| 6, 8 | Rich, 30x30 | Teach the same distinguishing relationships on a large canvas |
| 1, 3, 5, 7 | Varied, at least one side 21..30 | Add rectangles, distant seeds and longer active keys |
| 9 | Varied, 9..18 | Retain smaller complete, edge and free layouts |

Always drawing 30x30 would remove exact canonical support. Uniformly drawing all
sizes would make the required canonical profile rare and give no per-lesson
teaching guarantee. Expanding only blank borders would provide weak new reasoning
coverage. The retained boundary probe instead includes 30x30 corners and center,
30x9, 9x30 and 21x29 cases, exact far-edge seed locations, and long active keys.

Measured at seed 735, indices 0..99, independently for each band: 30/100 exact
16x16, 20/100 exact 30x30, 60/100 with a side above 20, 47/100 rectangles, and no
invalid inputs. These counts are for that explicit finite recipe. The strict
profile gate uses 20 draws per band and records exact/envelope hits of 6/20,
6/20 and 5/20, totaling 17/60; its thresholds are unchanged. The override gate
executes 41,760 attempts across 464 cases, three bands and 30 seeds: 35,100
accepted calls, 6,660 explicit incompatible-tuple rejections, zero findings,
zero warnings. Its compact report omits per-success rows and says so explicitly.

## Teach complete lessons and report the actual assembly

The old alternating rich/varied phase is retained; its combined dimension/phase
period is now declared as 10. Rich examples carry a repeated key color, an
internal zero, and top clipping, distinguishing four canonical-compatible
shortcuts plus six additional semantic rivals. Four consecutive default phases
contain two rich examples before any sampler rejection/deduplication. We still
check actual materialized production lessons rather than assuming that raw-call
argument proves the exported lesson's behavior.

Current policy is three demonstrations and one query. Production keeps their
order; the required rotation policy holds out each of the four labeled pairs
once and preserves the remaining order. This review does not reuse the prior
notes' four-demonstration/five-pair measurement.

The successful random census has 100 lessons per band: 300 materialized lessons,
1,200 unique inputs, zero ambiguous production lessons, and zero ambiguous
rotations among 1,200. Seeds follow the retained native SHA-256 task/band/index
recipe and indices 0..99 per band. It is finite random coverage, not an exhaustive
schedule proof. Separately, seed 0 and every start residue 0..9 across the three
bands give 30 overlapping lessons, 120 pair occurrences and rotations, and only
21 unique inputs; all pass. Overlapping windows are not counted as independent
samples. The final semantic gate consumes that exact schedule receipt and passes.

An earlier random-census attempt stopped after 266/300 materialized lessons
because the shared filesystem ran out of inodes while writing a temporary
runtime report. Its zero observed ambiguity is not counted as a pass. Both its
full failure and the completed retry are retained losslessly as native gzip
receipts, with original-path/size/hash manifests and unmodified summaries.

**Shortcut self-review:** The rich phase still correlates informative features
with a top-near seed and selected sizes; the varied phase and canonical anchors
reduce this restriction, but do not prove a trained model will avoid it. The
38 Racket boundary cases, 300-lesson census and all-start fixed-seed census refute
the declared alternatives within their measured scope; unknown alternatives,
nonconsecutive subsets and arbitrary overrides remain outside that claim.

## P1: one episode-level metric parameter

The suitable parameter is `ring_metric ∈ {chebyshev, manhattan}`. It preserves
key positions, color roles, seed location, separator, header-marking semantics,
and the reasoning sequence from distance to color. Both metrics have the same
axial extrema, so the complete-ring boundary test remains applicable. The
canonical setting uses the exact canonical Racket text, not a rewritten mirror.
The proposed setting changes a single uniquely matched distance expression.

Chosen once per episode, the setting is determined by the seed parity unless an
explicit valid override is supplied. Input sampling does not depend on the metric.
Two retained seeds, 2026102300 and 2026102301, cover both settings with three
demonstrations at 16x16, 19x21 and 23x27, plus a 30x30 query. Query keys use
16..20 positions in the prototype's separate 1..20 domain, so the larger example
exercises meaningful additional rings. The selected canonical generator keeps
its 1..10 key limit.

The build records 47 Racket executions, six stored canonical comparisons (three
unique pairs), eight episode-input default-authority comparisons and three
boundary comparisons. The same-input metric witness differs in 54 cells. Both
episodes refute the other metric and nine semantic rivals before their queries.
The identity-only demonstration negative control is intentionally ambiguous and
is rejected by the checker. That is a test fixture, not a natural solve failure.

The prototype has two settings and two retained episodes, not a broad randomized
variant census. Variant rotation guarantees and training benefits are unknown.
All public/private boundaries are explicit and hash-verified. Program hashes:

| Setting | Exact Racket source SHA-256 |
|---|---|
| chebyshev | `f81bb3fa88d32b94f168da64f163cdca3238224ce674640c99df1ec7320184cf` |
| manhattan | `e12b9c999ed2d5c5ff35117d5db16ce88ff1bc1aabbf7654b1cae3ac03770f13` |

Evidence: `checks/parametric/evidence-final/`,
`checks/parametric/retained-verification-final.json`, and the prototype README.
Status is **prototype/proposed**, with no source, variant or training approval.

## U1/U2: make reusable tools fail honestly

Independent review reproduced stale episodes surviving a rebuild into a nonempty
prototype export directory. The exporter now refuses such destinations before
writes or runtime startup. A genuine red test preceded the fix; the final 11-test
prototype suite and independent byte-preservation check pass. The old clean
two-episode bundle remains available as before-fix evidence; the current bundle
was generated in a fresh `evidence-final/` directory and binds current sources.

The boundary probe originally could label a report passed when the independent
model agreed but a reference-domain diagnostic failed. It now includes default
self-check failures, reference validity/errors and reference-domain failures in
its verdict. Independent injected failures prove both new rejection paths with
38 model matches still present. No production labels were changed. See
`checks/code-review.md`, `checks/code-review-postfix.py`, and its JSON receipt.

## F1: preserve the task distribution; propose the shared sampler repair separately

The stock defect linter couples seed and index: `generate(sd, sd)`. Therefore
`(seed + index) % 2` is always even and all 24 requests reach the rich phase.
Its limited-axis and persistent-marker warnings do not measure the varied phase.
Changing the task to accommodate this diagonal sample would hide the shared
measurement error and weaken its teaching design.

The optional patch instead uses seed 1 and consecutive indices at the same
budget, records exact requests, and reports partial schedule-residue coverage.
It changes no detector or threshold. The final ten-slot schedule is only partly
covered by eight requests per band; the patch does not turn that into a complete
coverage claim. It also trades away cross-seed sampling. A maintainer should
assess that general policy before adopting it; the stock-tool result remains
the official unresolved gate in this return. Concrete targeted evidence and
the isolated full-candidate integration attempt are in `checks/linter-proposal/`.

## Scope, solve honesty and handoff

The blind solve was completed before selected-generator or rule inspection.
The post-repair solve is explicitly exposed, uses the final generator bytes,
and was completed without consulting reference material during that solve.
Both match three visible examples; masked queries remain independently unscored.
Notes are reviewer work logs, not token-level model traces.

The two assigned audits are findings-only. Their sources remain unchanged;
`AUDIT.md` distinguishes actual Racket-backed control/domain defects from a
suspected transfer shortcut and from untested lesson ambiguity. No model was
trained, no approval record was altered, and no training admission is asserted.

The official delta is replayed on a fresh runtime-closure extraction of the
original ZIP, followed by tests in that checkout's own environment. This is
explicitly a selected-task dependency closure, not a second full corpus checkout.
The closure contains 354 of 100,447 original files; all nine changed-file hashes match, and the fresh checkout passes 180 tests plus 9 subtests. The final replay and test receipts are retained under `checks/replay/`.
