# d2b3402dde86 — current generator account

## Intended rule and authority

Crop the input to the minimal nonzero bounding box. Return the upper-left
rectangle with height `floor(content_height / 2)` and width
`floor(content_width / 2)`. Preserve every zero inside that rectangle, including
a completely blank outer row or column. Zero is background; foreground color
identities have no semantic ordering.

Selected version: `2.2.0`. Final source SHA-256:
`3b78ce8cacd3145d54c2158b77d54c3030f8aab4026264711bc3944e83b77f6c`.
`RULE_HASH=115e212b540d` is unchanged. This review made no canonical-data or Racket
source change. Active selected authorities remain synchronized; the historical
archival raw source remains text-divergent with execution parity.

## Current distribution and controls

`scene_profile` exposes all nine content-box origins in `{1,2,3}².
`extent_profile` is exact and observable:

- `canonical`: 6×6 content on 10×10 canvas;
- `even`: all pairs from `{4,6,8}²` except 6×6;
- `odd`: 5×9, 7×9, 9×5, or 9×7.

The default extent cycle is `canonical, odd, even, odd`, shifted by `seed % 4`.
Canvas dimensions are independently `max(10, content_dimension + 4)`.
Easy/medium/hard vary occupied-cell count and foreground palette size, not the
rule. The strict canonical schedule fraction is 25%; `MIN_STRICT_FRAC=0.20`.

The public call contract now rejects bool or negative seed/sample indices and
accepts only `None`, `easy`, `medium`, or `hard` difficulty values. Exact
`scene_profile` and `extent_profile` overrides remain supported.

## Current teaching schedule and competitors

The retained audit lead
`counterexamples/review-4bfe455c92aabee9-v0001/retained/checks/audit/d2b3402dde86/axis_trim_census.json`
showed that row-only or column-only output trimming could fit three demos and
change the query. Version 2.2.0 declares both rivals explicitly:
`trim_zero_rows_only` and `trim_zero_cols_only`.

Default answer-border features alternate by
`(sample_index + seed // 4) % 2`: forced blank top, forced blank left. Thus each
consecutive four-pair window has two witnesses for each axis-specific trimming
rival, and every single held-out query leaves at least one witness of each type
in the three demonstrations. The extent and border phases vary independently
across the eight relevant seed phases.

Other declared competitors include fixed 3×3, ceil-half, capped-three,
height-derived square, width-derived square, wrong corner/window, identity,
full crop, modal fill, and full background trimming. `lesson_identifiable`
reports only rivals that fit all supplied demos and predict a different query.

Final source-bound evidence:

- `counterexamples/axis_trim_repair.json` — compact prior finding, exact Racket
  witness, repair, and limits;
- `tests/test_axis_trim_and_call_contract.py` — cyclic starts, seed phases,
  query rotations, and strict scalar contract;
- `workspace/probe_distribution.py` — dynamic declared-rival census;
- `checks/lesson-census-final.json` in the review return — 300 production
  lessons and 1,200 rotations with zero ambiguities or scoring/hook errors.

## Proposed parametric extension

`workspace/parametric/` proposes one fixed-per-episode parameter, `corner`, with
values `upper_left`, `upper_right`, `lower_left`, and `lower_right`.
`upper_left` is the canonical default. The crop and independent floor-halving
reasoning are preserved; only the selected corner changes. Generated prototype
inputs make all four corner windows distinct. This is a task-local proposal,
not selected execution authority, catalog approval, or training admission.

## Known limits and open questions

The teaching guarantee assumes exactly three demonstrations plus one query from
four consecutive generated pairs. Arbitrary filtering, nonconsecutive sampling,
reordering, fewer demonstrations, or explicit extent-only curricula must be
rechecked. The deterministic alternation is structured and does not refute
order-index-dependent meta-rules outside the per-grid competitor interface.
Finite declared-rival evidence is not universal induction.

Generated support remains bounded: selected content dimensions, external zero
padding, three through five foreground colors, multiple colors in the answer,
and distinct corner windows. Border-touching content, unrestricted dimensions,
monochrome answers, and the entire executable reference domain are not claimed.
No model trajectory is admitted to training by these checks.

---

# Retained prior review history (superseded where the current account differs)

# Decisions for d2b3402dde86, review-4ac7928abb740d9e

## Objective and source

Teach the selected content-relative floor-half rule, preserve canonical
examples and exact controls, and return source-bound evidence. Baseline SHA-256:
`5611ca7a40482e8a099c52dec7fb2998112362ccc80dd3aadb0707f98f76e765`.
Final SHA-256: `2604e5d8f9f7d1500cc872527e43c43e80b7aee7d2228ad0d1785dd779cf1359`.

The imported associated notes from `external-local-random:09122ddcde35` were
used as a lead for the fixed canonical geometry and source-text divergence.
Their old results were not treated as measurements of this packet. No current
task-local test files or unresolved audit index were present at the draw.
The immutable assignment and blind-solve target were never changed or redrawn.

## D1 — Preserve the operation; widen content geometry

**Prior choice:** 10×10 canvas, 6×6 content, 3×3 answer, all bands. Imported
rationale: avoid inert or contradictory size controls while keeping canonical
teaching shape. This also made “crop to content, then always take 3×3” succeed
throughout generated support and on all three canonical labels.

**Decision:** retain canonical examples in one quarter of the default sequence;
add even dimensions from {4,6,8}² excluding (6,6), and odd rectangles (5,9),
(7,9), (9,5), (9,7). Add one observable `extent_profile` control. Preserve the
nine-position `scene_profile` control. The canvas uses independent
`max(10, dimension+4)` bounds, allowing every declared position to coexist
with every extent class.

**Alternatives:** all-canonical remains insufficient for size dependence;
unconstrained arbitrary shapes would dilute canonical support and require a
larger teaching contract. Odd square-only examples cannot distinguish use of
height for both output dimensions. Tiny-only examples cannot refute a 3×3 cap.
The selected odd rectangles refute all five dimension shortcuts at once.

**Evidence:** all three canonical labels remain accepted; 81 joint band/scene/
extent cases pass; all five emitted witnesses in `checks/final-witnesses/`
have matching official Racket outputs. The final census binds 1,200 unique
inputs to the final source and unchanged transformation.

**Limits:** generated support is bounded, excludes mixed-parity dimensions,
and couples canvas size to content extent. Arbitrary outer padding, objects
touching canvas borders, monochrome output and unrestricted grid dimensions
are not claimed. The strict hook retains canonical density and quadrant
conditions; self-check recognizes a broader lawful texture set.

## D2 — Preserve palette/density support without assigning colors a role

**Prior choice:** easy/medium/hard use 20/22/24 occupied cells and 3/4/5 colors
on 6×6 content. Each canonical quadrant contains five or six foreground cells
and at least three colors. The exact original motivation beyond the imported
canonical-support rationale is unknown.

**Decision:** retain those canonical settings. Scale total occupancy by area
for noncanonical boxes, while sampling foreground colors from all colors 1–9.
Zero remains the rule's fixed background. Require at least two foreground
colors in the returned region and distinct alternative windows to supply
direct counterexamples to modal fill and wrong-window rules.

**Alternative rejected:** forcing five colors into every small returned window
is impossible for a 2×2 answer. Global palette size remains exact; output
palette can be smaller. Tests independently count emitted palette colors.

**Limits:** density and asymmetry are teaching choices, not claims about the
entire executable reference domain. They exclude visually degenerate instances.

## D3 — Restore blank answer borders and teach their preservation

**Prior choice:** each quadrant independently touched its own relevant outer
edges. It guaranteed every generated answer had nonzero top/left support.
The canonical test instead has a completely blank answer top row.

**Decision:** require real support only for the complete content box. Deliberate
top/left blank-answer variants allow other regions to establish the box edges.
The output retains those zero cells and is never cropped a second time.

**Failed iteration retained:** the first repair selected these variants
randomly. On seed 0, medium, indices 2–5 with query position 1, the trimming
rival matched every demonstration and changed the query. All four labels were
confirmed by official Racket apply. Exact input, labels, rival and intermediate
source are retained under `checks/iterations/`; the four failing regression
cases and their JUnit evidence remain under `checks/regression-green-1.*`.

**Repair:** blank-border witnesses alternate by sample index. Their phase uses
`seed // 4`, independently of the extent cycle's `seed % 4`; across seeds,
odd size does not uniquely determine border style. Each four-pair window has
two forced border witnesses, so any single holdout leaves one in the demos.
Unforced slots remain free to contain or omit blank borders.

**Limit:** per-seed schedule parity remains structured. Cross-seed phase
variation is not a claim of statistical independence within one seed.

## D4 — Distinguish equivalent hypotheses from ambiguous query answers

**Prior choice:** reject any rival surviving every demonstration, even when it
predicts the same query. The old eight rivals were already individually
refuted by all canonical labels, leaving actual canonical ambiguity untested.

**Decision:** explicitly declare fixed-three, ceil-half, capped-three and
height/width-derived square shortcuts. Keep the original window/color rivals
and add answer trimming. Reject a lesson only when a surviving rival changes
the query answer; retain diagnostics for rival errors and wrong supplied labels.

**Test correction:** the first equivalent-survivor test assumed two canonical
demos determined the canonical test answer. That is false for answer trimming:
its 2×3 prediction removes a correct blank row. The revised positive test gives
all three canonical labels before a new canonical query; a separate negative
test preserves the discovered two-demo ambiguity. This fixes the test's premise
and adds coverage; it does not suppress the genuine failure.

**Assembly:** three demonstrations plus one query, drawn as four consecutive
pairs. Extent cycle C/O/E/O has two odd witnesses. Border cycle has two forced
border witnesses. Holding out any one pair leaves both kinds in demos; every
generated grid separately distinguishes the original eight rivals. The final
Racket census checks 300 production lessons, 1,200 actual single-query rotations,
and 1,200 unique inputs with no ambiguities, hook warnings or scoring errors.
The reusable mirror-only probe separately checks every start 0–39 for seed 17
in each band, giving 120 windows and 480 holdouts. Counts refer to overlapping
windows; they are not additional independent training examples.

**Limits:** finite named-rival evidence is not universal induction. Arbitrary
lesson reassembly, filtered indices, fewer demonstrations, or explicit extent
overrides must be checked under the actual downstream assembly policy.

## D5 — Resolve active Racket text drift without changing semantics

**Prior state:** the baseline battery had 10 green and 2 failed stages:
`defect_lint` and `authority_sync`. Canonical, selected and archival rule forms
executed consistently but active texts differed. The imported notes warned
against discarding explanatory comments merely to obtain exact equality.

**Decision:** set only this canonical row's `program_solution` to the existing
commented selected `target_code`. Preserve its comment and leave archival raw
source untouched. The canonical single-binding `let*` becomes equivalent
`let`; the normalized pin changes from `ba71279d2c14` to `115e212b540d`.
All other canonical rows and the base authority file remain byte-identical.

**Evidence:** `checks/authority-sync/repair-manifest.json`, original texts,
and the official parity receipt. Final battery: 12 green, zero warnings or
advisories. A failed direct-layout checker invocation remains recorded; the
supported public wrapper subsequently passed.

## D6 — Retain a reusable probe and verify portable execution

`workspace/probe_distribution.py` reads actual declared rivals dynamically,
checks canonical fit, geometry, strict support, palettes, blank answer borders,
unique inputs and every requested query holdout. It retains small counterexamples
and source hashes, preserves existing output files, bounds counts, and emits
nonzero status with a failure report. It explicitly labels Python mirror data
as diagnostic; Racket evidence comes from the public apply/census tools.

There are 110 generator-contract cases and six real CLI cases. They cover
observable behavior and independent expected geometry rather than source text.
Five CLI cases failed before the tool existed; their original logs remain.
The isolated task-test stage passes 116 cases with zero skips/errors/failures.

The first after battery retained one lint warning for computed AXES metadata.
The valid-value list is now a literal, and the entire final battery/census were
rerun on the final hash. The earlier 11/12 battery and earlier-source census
remain evidence, not substitutes for final-source results.

The portable test preflight initially found pytest only in the host's user
site. An offline venv copies the already-installed pure Python test packages
and keeps `PYTHONNOUSERSITE=1`; versions and a reproducible helper are retained.
A wrong relative interpreter path was corrected after the wrapper's explicit
repo-cwd error. Neither environment problem was counted as a passing test.

## D7 — Solves, audits and stopping condition

The untouched blind solve (`4296e507c770`) was completed before opening any
task implementation: one revision, 3/3 visible examples, earlier exposure no.
The post-repair solve uses the exact final generator: one revision, 3/3 visible
examples, earlier exposure yes. Neither solve consulted a reference during
the solve; query correctness remains withheld. Notes are authored work logs,
not token-level traces. No artificial failed solve was created.

Both assigned findings-only audits retain exact sources and Racket evidence
under their own task headings in `AUDIT.md`. They do not change the audited
generators or approve them. No external service, repository or competition
submission was written. Final completion requires fresh-packet patch replay,
matching source hashes and the focused tests, as recorded in `RESULTS.json`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4bfe455c92aabee9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `2604e5d8f9f7d1500cc872527e43c43e80b7aee7d2228ad0d1785dd779cf1359`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve prior2604e5d8 axis-specific answer-trim finding on3b78ce8c repair:row-only/column-only rivals declared andblanktop/blankleft alternate,twowitnesseseach pereveryfourpairwindow.140local/fullfresh replay tests,12/12finalbattery,300lessons/1200rotations and768cyclic heldoutchecks reportclean. Canonical Racket unchanged;finite declared-rival evidence,notuniversalidentification.

### Assessment or prior finding

## d2b3402dde86

**Reproduced teaching defect — axis-specific answer trimming can survive three
demonstrations and change the query.** The intended rule crops to the nonzero
content box and returns the upper-left floor-half. The generator schedules two
blank-answer-border witnesses in each four-pair window, but each witness chooses
`blank_top` or `blank_left` independently. The declared `trim_answer_background`
rival removes both axes at once; a demonstration with either blank axis refutes
it. A more specific rival can remove only all-zero output rows or only all-zero
output columns.

Concrete case: difficulty `easy`, seed `0`, window start `0`, held-out offset
`2` (sample indices `0,1,2,3`). The **column-only** trimming rival fits all
three Racket-labelled demonstrations but removes the blank left column from the
held-out query. All four inputs pass the generator domain check, and the
canonical Racket outputs match the retained labels. The receipt binds rule hash
`115e212b540d` and generator SHA-256
`2604e5d8f9f7d1500cc872527e43c43e80b7aee7d2228ad0d1785dd779cf1359`.

A broader source-bound mirror census covered three bands, seeds `0..99`, 17
four-pair starts per seed, and all four holdouts: **20,400 rotations**. It found
**4,352 ambiguous holdouts**—2,236 against column-only trimming and 2,116
against row-only trimming. Reproducer:
`checks/audit/d2b3402dde86/reproducer.json`; supporting evidence includes
`axis_trim_counterexample.json`, `axis_trim_racket.json`, and
`axis_trim_census.json`. The isolated current task-test stage passes **116/116**
at `checks/audit/d2b3402dde86/task-tests/result.json`. No target source was
edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-4bfe455c92aabee9-v0001/audit_assets.json), manifest SHA-256 `7bfb0f2fc368f88291a5d825e34f24be48f9584cfb5d2b31e395e52ad91168f6`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `3b78ce8cacd3145d54c2158b77d54c3030f8aab4026264711bc3944e83b77f6c`.

# Decisions — d2b3402dde86 / review-5c46645ed6c0bf24

## D1 — Treat the retained axis-trimming audit as the primary repair

**Prior choice and rationale:** Version 2.1.0 deliberately generated blank
answer borders, but the schedule only guaranteed a generic blank-border witness.
The exact reason for not separating row-only and column-only trimming in the
selected baseline is unknown. Prior audit `review-4bfe455c92aabee9:v0001` showed
that one-axis trimming could survive all three demonstrations and change the
query.

**Decision:** Add `trim_zero_rows_only` and `trim_zero_cols_only` as executable
lesson competitors. Alternate forced `blank_top` and `blank_left` answer-border
features so each consecutive four-pair window has two of each. The phase is
`(sample_index + seed // 4) % 2`, separate from the extent cycle's
`(sample_index + seed) % 4` phase.

**Alternatives considered:** Randomly request top/left borders; only add rivals;
reject lessons after generation. Random placement does not guarantee a witness,
and declaration alone merely detects rather than prevents weak lessons.
Post-generation rejection can distort indices and reintroduce schedule gaps.
The deterministic schedule gives a direct three-demo guarantee under the actual
consecutive-window assembly.

**Probes and evidence:** The red-first test found seed 0/easy/start 0 had only one
column witness. After repair, all seed phases 0..7, starts 0..7, bands, and four
query positions pass. `checks/distribution-final.json` extends this to 64 starts
per band; `checks/lesson-census-final.json` checks 300 production lessons and
1,200 query rotations with zero ambiguities.

**Failure modes and limits:** The guarantee assumes four consecutive generated
pairs with exactly one held out. Reordered, filtered, independently sampled, or
shorter lessons are not covered. Named rivals do not exhaust all hypotheses.

## D2 — Make invalid scalar rejection explicit at the public boundary

**Prior choice and rationale:** The baseline delegated scalar handling to shared
context utilities. The exact original rationale is unknown; current defect lint
showed that Python equality and downstream coercion allowed bools, negative
indices, and non-enumerated difficulty values.

**Decision:** Validate `seed` and `sample_index` as nonnegative exact integers
(`bool` rejected), and difficulty as exactly `None|easy|medium|hard` before
constructing `GenCtx`.

**Alternative considered:** Patch shared `GenCtx`. That would affect unrelated
generators and exceeds this task-local assignment. Task-local validation is
small, observable, and fully covered.

**Evidence:** Before defect lint reported 30 warnings. Final defect lint reports
`FLAGGED 0`; the focused parameterized regression covers ten invalid calls.

**Limit:** This is a task-local contract. Other generators need their own repair
or a separately reviewed shared policy.

## D3 — Preserve the selected Racket authority

**Prior choice and rationale:** The selected canonical program already performs
crop-to-content followed by the upper-left independent floor-half. It passed
rule smoke and authority sync; the archival raw source is an equivalent but
text-divergent historical form.

**Decision:** Do not edit canonical data, selected Racket text, `RULE_HASH`, or
reference labels. The repair is entirely in generated input scheduling,
competitor declarations, validation, tests, and task-local tooling.

**Alternatives considered:** Rewriting comments or normalizing the archival
source would add authority risk without solving the teaching defect.

**Evidence:** Final `rule_smoke`, `racket_lint`, and `authority_sync` are green;
`RULE_HASH=115e212b540d`. Authority sync records selected active authorities as
synchronized and the existing archival source as divergent with execution parity.

## D4 — Propose one bounded parametric extension: selected corner

**Assessment:** A suitable small parameter exists without changing object roles
or reasoning structure. After cropping to nonzero content, select one of
`upper_left`, `upper_right`, `lower_left`, or `lower_right`, keeping independent
floor-sized dimensions. `upper_left` is the canonical default.

**Decision:** Keep a separate runnable prototype under
`workspace/parametric/`. Choose one setting once per episode via a deterministic
SHA-256-derived seed. Use three demonstrations and one query; require every
input's four corner windows to be distinct. Public challenge files omit hidden
metadata, program text, and query answers.

**Alternatives considered:** Parameterize floor versus ceil or output dimensions.
Those alternatives overlap known canonical-compatible shortcuts and risk
changing the core dimensional lesson. Corner selection preserves crop,
independent halving, and spatial-window reasoning with one easy-to-observe choice.

**Evidence:** `checks/parametric/corner-verification.json` runs four programs on
four retained episodes in one Racket session, checks all 16 combinations,
Python/Racket parity, and all pairwise demonstration/query disagreements.

**Failure modes and limits:** Only four settings and retained seeds are checked.
The prototype is proposed, not catalog-approved, integrated, or training-admitted.

## D5 — Retain reusable source-bound evidence rather than only prose

**Decision:** Keep the dynamic distribution probe, focused tests, canonical
Racket shortcut receipt, compact repair counterexample, parametric verifier,
and audit reproducers. Commands refuse to overwrite final output files and bind
reports to source hashes.

**Alternatives considered:** Copying full controller logs into task notes or
relying only on the general battery. The first is noisy; the second does not
exhaust cyclic starts or preserve exact shortcut examples.

**Evidence:** Paths and counts are indexed in `REVIEW.md` and `RESULTS.json`.

**Limit:** Python mirrors are explicitly diagnostic. Claims about official labels
use Racket receipts or official check/census stages.

## D6 — Stop after a green final source and document structured-order risk

No generator change was made after the final battery, lesson census, or exposed
solve preparation. The remaining known risks are bounded-domain coverage,
undeclared rivals, and dependence on consecutive ordered four-pair assembly.
These are documented rather than hidden behind a universal identifiability claim.

## Parametric upgrade — review-5b7b5236332485e6

The retained corner proposal is now a native, source-bound adapter rather than a
one-query sketch. `workspace/parametric/` exposes `corner=upper_left|upper_right|
lower_left|lower_right`; `upper_left` remains byte-exact canonical authority.
Input sampling is independent of the hidden corner, supports 2–6 demonstrations
and 1–4 queries, and keeps query prefixes stable. Every sampled grid makes all
four floor-half windows distinct. The fourth query is a substantive 30×30 input
with a filled, textured content box rather than padded small content.

Sequential public turns contain all demonstrations and only the current query
input. IDs hash those exact visible bytes; settings, programs, future queries,
total-count hints and query answers remain private. The verifier rejects bad
counts/settings, duplicate inputs, tampered labels and program mismatches.

Fresh bounded evidence: 156 task-local tests passed; protected Racket executed
four programs over seven retained inputs; the native inventory is
`workspace/parametric/evidence/manifest.json` with SHA-256
`cda904c13dbe9b5794bfdc4a472c016efe96fe88d33663879bb22801d49a3726`.
This remains a proposed family, not owner qualification or training admission.
