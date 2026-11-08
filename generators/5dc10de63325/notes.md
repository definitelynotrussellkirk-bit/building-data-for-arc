# Working notes: 5dc10de63325

## Version 4.0.0: domain and authority

This repair keeps the selected Racket rule, hash `f2b1ab0d6fcb`. Count every cyan cell, compute `q = count // 4`, and repeat the fixed q-cell glyph in the four 2×2 quadrants of a 5×5 zero-cross output. Ordinary generation covers counts 4–19, hence exactly four nonempty outputs.

The canonical ledger contains 14 labeled records, seven unique pairs, all 6×6 with cyan counts 12 or 16. A disconnected 6+6 case establishes that connectivity is not a domain requirement. Counts 4–11, 13–15, and 17–19, and dimensions beyond 6×6, are deliberate rule-supported extensions rather than additional canonical observations. Legal four-cell lines and solid 2×2 blocks are retained because the task depends only on total count.

Final generator SHA-256: `1a589702f4362e710cb8bae47b2197349db3037274e702a8b0fa9f9736bb34e9`.

## Exact controls

| Control | Contract |
| --- | --- |
| `grid_h`, `grid_w` | Exact Python integers in 5–18, in every difficulty band |
| `n_cyans` | Exact Python integer in 4–19; no clamping |
| `distribution`, `texture` | `clustered`, `row_aligned`, `block`, `snake`, or `scattered`; both aliases may be supplied when they agree |

Unknown controls, invalid types and bounds, and conflicting aliases raise `ValueError`. The formerly ineffective `anchor_corner`, `asymmetry_force`, and `include_decoy` controls are removed, as is `force_div_4`; request an explicit divisible count when needed. Boolean, floating-point, string, and `None` values are not integer overrides.

`texture="no_cyans"`, `"full_grid"`, and `"single_cyan"` remain explicit diagnostic fixtures outside the ordinary values advertised in `AXES`. They fail the lawful input check and cannot be combined with an exact `n_cyans` request. Ordinary draws mix canonical-size and broader grids in every band; difficulty biases dimensions without narrowing explicit controls.

## Ten-demonstration curriculum

Use **ten demonstrations and one query**: `--train 10 --test 1` in the CLI or `n_train=10, n_test=1` in Python. The public generation default remains three demonstrations; declaring `EXAMPLES_NEEDED = 10` does not change that API default.

Each seed receives a cycle of independently shuffled `(q1, q2, q3)` blocks with optional q4 slots, a random phase, and a direction. Low buckets alternate protected remainders 2/3 with free remainders 0/1; q4 can use every remainder. Opposite remainder classes have different counts and therefore cannot become duplicate input grids. This final change addresses the retained seed-319 failure where duplicate removal previously lost a repeated low-glyph witness.

An eleven-draw contiguous schedule window contains at least two examples of each nontrivial glyph, q1–q3, and protected rounding examples. Holding out any one pair therefore retains demonstrations that distinguish the declared rounding and glyph-order rivals. Independent block permutations and optional q4 slots avoid the earlier fixed four-bucket order and fixed seven-slot histogram. Explicit count overrides replace this curriculum scheduling.

This schedule claim concerns raw consecutive draws and declared rivals. Accepted lessons are assessed separately below. Custom rejection filters, arbitrary resampling, shorter lessons, and external deduplication policies require their own checks. Counting all nonzero cells is equivalent on the supported `{0,8}` domain. A fixed 6×6 crop is canonically compatible and is not a guaranteed-refuted rival.

## Retained verification and limits

The review packet's `checks/task-tests-dedup-final/` records **286 passed**, including exact controls, malformed inputs, canonical support, every declared count, schedule holdouts, and the seed-319 duplicate regression. `checks/regression-red/` retains the earlier failing control tests.

The following distinct checks bind to the final source above:

- **Raw cycle probe:** `checks/curriculum-final.json` exhausts all cycle starts for seeds 0–19 in the medium band: **557 raw eleven-pair windows and 6,127 single-pair holdouts**, with no declared-rival ambiguities or domain violations. It observes every count 4–19. `materializer_applied=false`: no duplicate or identity filter is applied. The oracle uses independent literal glyphs calibrated against all 14 canonical labels and does not execute Racket.
- **Public materialized-lesson census:** `checks/lesson-census-final.json` records **300 accepted lessons**, 100 per band, containing **3,300 pairs and 3,062 unique inputs**. No declared-rival ambiguity was found in the 300 production query positions or 3,300 single-pair rotations. There were no materialization or scoring errors.
- **Independent accepted-window sweep:** `checks/code-review/dedup-after-window-sweep.json` checks **33,786 accepted windows** across seeds 0–399 in all three bands. It mirrors the runner's duplicate and identity filters using calibrated literal glyphs. **121 windows involved duplicate removal; no identity removal or support failure was observed.** Every checked accepted window retained at least two examples of each q1–q3 glyph and three protected rounding examples.
- **Racket-backed duplicate regression:** `checks/code-review/dedup-after-reproduction.json` replays seed **319**, start index **1**, medium difficulty, through the unchanged runner using outputs retained by public canonical Racket execution. It accepts source indices 1–10 and 12, rejects duplicate index 11, and passes all eleven query rotations.

Separate public Racket evidence in `checks/racket-counts/final-racket.json` covers 34 inputs, including the lawful minimal shapes. The raw probe, independent filter sweep, and actual materialized lessons provide different evidence; none establishes behavior under every possible external filtering policy.

The final twelve-stage battery in `checks/after-dedup-final/` completed with **exit 1: eleven green stages and one failed stage, `defect_lint`**. Its `selfcheck-minimal-impostor` warning concerns accepted short-line and solid-2×2 probes. These four-cyan shapes are lawful counting inputs; their Racket outputs and focused tests provide the requested semantic evidence. The warning remains a reported gate failure, with no exemption or shared-tool change. Finite named-rival checks do not establish universal identifiability.

Imported provenance remains in `evidence/associated_notes.jsonl`. Runnable commands and tool options are in [workspace/README.md](workspace/README.md).
## Review review-c3afe81e1498601e: parametric fill-order prototype

This review leaves the selected production generator and canonical Racket authority unchanged. The generator remains version 4.0.0 with SHA-256 `1a589702f4362e710cb8bae47b2197349db3037274e702a8b0fa9f9736bb34e9`; the canonical rule remains hash `f2b1ab0d6fcb` and source SHA-256 `7a10e356fef67a39818753dde5902520c4f89b1bf646ada192200eb0da0ec8a3`. The prior repair already provides broad lawful geometry, exact controls, protected curriculum scheduling, and explicit semantic rivals. Narrowing the domain to reject four-cell lines or 2×2 blocks would contradict the count-only rule, so the shared `selfcheck-minimal-impostor` warning is retained rather than hidden.

A separate runnable proposal now lives in `workspace/parametric/`. It selects one episode-level `fill_order` from three bounded settings: canonical `bottom_row_first`, `right_column_first`, or `top_row_first`. Every setting preserves the original reasoning chain—count cyan cells, floor-divide by four, fill a 2×2 glyph, and repeat it around the zero cross. Each episode uses q1, q2, and q3 demonstrations plus a q2 query; those demonstrations distinguish the chosen setting from both declared rivals. The default materializes to the exact canonical source bytes, all retained labels are generated by executed Racket, and the Python mirror is used only for parity checks.

Fresh evidence is under `checks/parametric/fill-order-v1/`: all three settings passed, the default replayed all 14 canonical records with zero mismatches, and every public challenge redacts the seed, hidden parameter, Racket text, rival outputs, and query answer. Portable task tests report **297 passed**. The fresh twelve-stage after battery reports **11 green stages and one failed `defect_lint` stage**, the same lawful-minimal-shape warning present before this review; lint, authority synchronization, rule smoke, self-check, profile floor, semantic, diversity, overrides, grammar, and Racket lint all pass. Exact profile support is 22/60. The semantic smoke check accepts 600/600 strict draws, 14/14 canonical inputs, all 5 witness/rival claims, 12/12 lessons, and all 132 diagnostic rotations.

The raw schedule probe covers 1,671 lessons and 18,381 single-pair holdouts across all three bands, all counts 4–19, and 44 declared rivals with zero ambiguities. The Racket-backed production census materializes 300/300 ten-demo lessons, checks 300 production queries and 3,300 query rotations, and finds zero ambiguities or scoring errors. Re-scoring those retained labels with seventeen context-only baselines finds no perfect predictor; the strongest measured baseline reaches 49.67% on production queries and 61.64% across rotations. These are finite declared-hypothesis checks, not a universal identifiability proof.

The proposed fill-order family remains isolated: it covers three settings and one retained episode per setting, does not alter training approval, and is not a production rule-selection API. Its builder, source pinning, Racket execution, redaction, hash manifest, and focused tests are intended as reusable task-local scaffolding for future parametric reviews.

## Current reviewer considerations

Source SHA-256: `1a589702f4362e710cb8bae47b2197349db3037274e702a8b0fa9f9736bb34e9`.

# Decisions for 5dc10de63325

Final generator: `1a589702f4362e710cb8bae47b2197349db3037274e702a8b0fa9f9736bb34e9`; selected rule: `f2b1ab0d6fcb`. Original generator: `5849bfee397072173f2f9f2627ab436e924d7be6251d70dc544d419f6e5ca65b` (3.3.0). The original author's intent beyond the retained notes is unknown; conclusions below come from code, canonical pairs, and actual probes.

## Domain and exact controls (R1/R2)

The immutable canonical ledger contains 14 labelled records across two variants, representing seven unique pairs. All are 6×6 with palette {0,8} and cyan count 12 or 16. One has two four-connected components of six cells. Connectivity therefore cannot be a validator requirement. The transformation counts all cyan, floor-divides by four, and repeats a fixed 2×2 glyph in a 5×5 output with an empty center row and column.

Counts **4–19** cover all four positive output glyphs and every remainder for each bucket. The old advertised 1–18 range was silently clamped to 4–18; accepting count 19 is an intentional compatible-rule extension, not recovery of an old promised override. Counts below four and at least twenty reach the reference's empty-glyph branch and remain outside the ordinary positive-output domain. Every count in the new interval was checked in two input geometries with public Racket. We kept lawful four-cell lines and blocks despite shared defect lint; changing the domain merely to clear that detector would conceal a valid case.

Height and width are independently exact Python integers in **5–18**, regardless of difficulty. Defaults use a 50:50 canonical-profile/broad-grid choice, with dimension weighting by difficulty; explicit controls bypass that choice. This addresses the old hard-band zero support for 6×6 without collapsing generation to the few canonical shapes. The final 20-draw-per-band profile check observed 9, 7, and 6 exact size/palette matches. Those are finite support observations; canonical size/palette alone does not imply canonical morphology.

The five supported geometries remain `clustered`, `row_aligned`, `block`, `snake`, and `scattered`. Their purpose is to vary arrangement while preserving exact global count. None promises connectivity. `texture` is an alias for `distribution`; agreeing aliases are accepted and conflicting aliases raise an explicit incompatibility. Non-Python-integer values, booleans, None, invalid ranges, and unknown names are rejected instead of coerced or clipped.

Remove `anchor_corner`, `asymmetry_force`, and `include_decoy`: each was observationally inactive in all 30 baseline comparisons in `checks/design/design_measurements.json`. The palette stays {0,8}, so no decoy-color distinction is claimed. Remove `force_div_4`, which otherwise changes an exact caller count; callers can request 4, 8, 12, or 16 directly. Deliberate `no_cyans`, `full_grid`, and `single_cyan` diagnostic textures remain callable outside ordinary AXES and fail lawful self-check; pairing them with an exact count is rejected.

## Curriculum and rejected alternatives (R3)

The canonical counts expose only q3 and q4. Five declared shortcuts genuinely fit all 14 canonical labels: ceiling, nearest-quarter rounding, a two-glyph threshold, column-first filling, and bottom-left-first filling. Canonical-fitting status is verified from the actual declarations rather than a copied list. `largest_component_only` is not such a shortcut because it fails the disconnected canonical case; counting all nonzero cells is equivalent within the supported palette.

| Design considered | Why it was rejected or retained | Evidence |
| --- | --- | --- |
| Baseline period-four outputs, three demos | Missing fourth glyph determines the query without looking at its input. | Baseline source and design measurements; by-construction output schedule. |
| Same period, four demos | Copying the first output determines the query. | Retained rejected-alternative analysis in raw probe. |
| Twenty-count schedule, four demos | q1 packing ambiguous in 8/100 holdouts, q2 packing in 13/100. | `checks/design/design_measurements.json: candidate_20_schedule`. |
| Fixed seven-slot histogram | Histogram complement determines the held-out glyph. | Raw probe's rejected alternatives. |
| Optional q4 but one shared low-glyph cycle | Ordered-context decoder reaches 92.31% across 158,496 grammar windows. | `checks/design/schedule/optional_q4_grammar_probe.json`. |
| Independent shuffled triplets, ten demos, overlapping remainder classes | Raw support looked sufficient, but actual deduplication erased the sole remaining q1 witness at seed 319/start 1. | `checks/code-review/dedup-before-reproduction.json`; actual red test. |
| Independent shuffled triplets, alternating disjoint remainder classes | Retained; preserves repeated count classes through duplicate-only filtering and distinguishes all declared rivals in the measured populations. | Final proof, regression, accepted-window sweep, public census. |

Each seed uses eight blocks with independently shuffled q1/q2/q3 and optional q4, then a seed-specific phase and direction. A mask with at least one included and one omitted q4 avoids a single fixed histogram. The cycle length is 25–31. Every eleven raw draws contain two complete adjacent blocks. Alternating low-bucket remainders {0,1} and {2,3} make the paired witness classes have different counts, so their first representatives cannot be identical grids. q4 keeps all remainders.

Ten demonstrations plus one query are sufficient for this grammar and the declared rivals; they are not claimed globally minimal. After one holdout, demonstrations retain all three nontrivial glyphs, distinguishing every alternative fixed fill order, and at least two protected rounding counterexamples. Duplicate-only preservation assumes a fresh seen set and successful collection. No proof covers arbitrary identity filtering, other rejections, or manually overridden count sequences; finite accepted-materializer checks are reported separately.

The public generation API still defaults to three demonstrations. Every intended export must pass `n_train=10, n_test=1` or `--train 10 --test 1`; semantic tooling reads the metadata, while ordinary generation does not. A future shared API fix is F3. Query-rotation testing uses every labelled pair once while preserving the remaining order. No distribution-free induction guarantee is claimed.

## Authority synchronization (R4)

Change only `/racket_target/target_code` in the two assigned base JSON files, copying the exact unchanged canonical program. Preserve `raw_code`, metadata, and all bytes outside each selected string. `checks/authority-sync/change-report.json` and `verification.json` record the surgical change and hashes. The canonical ledger SHA-256 remains `f5aa554e2aa0959cddca2a4a693e3524f8ad2836fbdff7f85a481058bcded6ee`. Selected authority text now has one group; archival raw code divergence remains disclosed and does not change executed rule behavior.

## Verification choices and limits

Keep the initial 108-failure control regression, the five-None-validation intermediate failures, the genuine seed-319 failing regression, all battery failures, and the earlier solves. A finite 300-lesson pass on the preceding candidate missed the duplicate case; this is why raw-window and accepted-window evidence are now separate. The reusable raw-cycle and saved-census context scorers complement the public Racket census without repeatedly generating labels.

The whole repository suite completed 403 passes and three optional-PyTorch skips, but it ran before the last generator correction and does not discover task-local tests. Final-source core tests are separately recorded, and the exact final patch receives a fresh-extraction replay. Additional hypotheses such as a fixed 6×6 crop and all possible context-only algorithms remain unproven. No training approval state is edited.

## Current production and prototype scope

Production `4.0.0`, source SHA-256
`1a589702f4362e710cb8bae47b2197349db3037274e702a8b0fa9f9736bb34e9`,
and canonical rule `f2b1ab0d6fcb` remain unchanged. Historical production
census, context-only checks and lint limitations above remain reported evidence;
this prototype-only change does not rerun or clear them. In particular, retain
the lawful count-only minimal-shape lint warning and all previously reported
malformed-call warnings rather than suppressing them.

The isolated **proposed** `workspace/parametric/prototype.py` is now
`fill-order-v2`, with the same three fill-order settings and exact canonical
default. Independent `--train 3..32` and `--test 1..32` controls replace the
fixed three-demo/one-query builder; defaults are three/four. The four-query
command and public/private contract are in `workspace/parametric/README.md`.
All inputs are checked for lawful exact counts and distinctness. Duplicate
sampling raises after 100 attempts per input, rather than returning too few.
A separate `--input-seed` is shared across settings in the gallery, so the
same count request compares identical input grids and ordering.

Concrete teaching repair: old demonstrations at counts 5/9/13 allowed nearest
quarter rounding, yet it disagreed on the count-10 query. A red regression and
a fresh canonical-Racket witness are in
`WORK/checks/5dc10de63325/rounding-red.log` and
`WORK/checks/5dc10de63325/final-tests.log`. New demonstrations at
7/11/15 teach floor division and q1/q2/q3 fill order; the four queries use
6/10/14/18. For each query, demonstrations alone select survivors among
100 analytical rivals: all 24 fixed fill orders combined with floor, ceiling,
nearest-quarter and two-glyph count policies, plus four constants. The current
retained episodes have one survivor and no query disagreement. A regression
mutates a query answer and confirms that demo-based survivor selection stays
unchanged. Rival predictions are analytical; every retained label and every
prediction of the three proposed settings is executed through matching Racket.

Public export now uses exactly shared `public_challenge_bytes` and
`public_challenge_id`: only demonstration input/output and query input grids
are written. This intentionally replaces the old task/schema/version envelope.
The old deep-copy exporter also leaked extra private keys nested in training
pairs; the new shared projection strips them. `red.log` reproduces this before
the change. Writer tests check exact byte/hash identity and invariance to
private metadata and query answers. Batch descriptors are sorted by public ID;
the writer explicitly rejects duplicate visible payloads before overwriting
an existing public file. Actual Racket writer regressions failed before both
corrections (`sorting-red.log`) and pass on the current source.

Fresh bounded evidence: `WORK/checks/5dc10de63325/four-query-current/` retains three
3/4 episodes at shared input seed 2026, and
`WORK/checks/5dc10de63325/five-demo-two-query-current/` retains three independent 5/2
episodes at shared input seed 17. Each gallery executes its 21 selected labels
and all alternative-setting labels through Racket, with canonical replay
14/14. Focused tests cover exact public bytes, requested sizes, all three
settings, query-only-answer mutations, and the 32/32 input-uniqueness boundary.
The 32/32 boundary is not a Racket label census. Exact commands, hashes and
final test count are in `WORK/checks/5dc10de63325/agent-result.json`.

This is a task-local prototype; production generation, canonical authority,
approvals, the shared parametric API, and training admission are unchanged.
The finite rival family does not prove uniqueness against arbitrary programs,
and two retained seed/count configurations do not establish exhaustive sampling
coverage. Earlier galleries and `agent-result-prior.json` remain prior-source evidence.
The prior manually authored argv resolved the virtual-environment Python symlink
to its base interpreter path; original commands used the literal venv path.
Current authoritative commands are captured directly by the launcher in
`final-tests-command.json`, `four-query-current-command.json`, and
`five-demo-two-query-current-command.json`, with literal venv payload paths.

## Current native count/component promotion

The native adapter reuses all three existing fill-order programs and adds
`largest_component_count`: segment cyan cardinal components, measure the largest,
then render the canonical quarter-count glyph. The exact default remains unchanged.
Native lessons require 4–6 demos. The retained protected-Racket regression shows
that the first three glyph demos admit global counting; demo four separates it.
This replaces neither the production ten-demo curriculum nor the legacy prototype.
The native 30x30 extension uses distributed cyan signal with dense noncyan clutter;
only 4–19 cyan cells are sampled because the canonical output branches are finite.
Bounded audit: 192 episodes / 1,728 label claims / 160 distinct grids / 581 policies,
42 protected executions, zero findings; full task suite 332 passed. These counts
are reviewer reports; native qualification and owner acceptance remain distinct.

Owner reconciliation: Five exact disjoint rules preserve the prior four-program family and four-demo minimum. Matched inputs vary total counts, component sizes, marker colors and order across seeds; queries are independently shuffled. Sparse 30x30 scenes span the canvas under the relay's lawful 4..19-cyan and exactly-four-marker grammar. Original samplers remain task-local. The exact prior programs and incoming alternate are preserved. Fresh source-bound acceptance and causal evidence: `evidence/owner-variant-reconciliation/current.json`.
