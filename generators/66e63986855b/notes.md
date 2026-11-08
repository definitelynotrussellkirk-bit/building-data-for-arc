# Working notes: 66e63986855b

## 2026-10-04 / review-014044c7e991126a

Baseline v3 SHA-256: `6493cddafa2f41ce449da8edec78bb1c40528c7c5a1be459371c4d089164cee3`.
Final v4 SHA-256: `8f78ef0944e40e80f9b86e9d5fdb2c9515fd05240e400d097e9993c5af79bc2f`.
Rule hash remains `e9ecd02cbe2e`.

Prior leads: the imported `evidence/associated_notes.jsonl` entries GNOTE-000430
through GNOTE-000434 and local-random-c28ce396ea35 describe the earlier v3 work.
These were leads, not substituted measurements. No earlier return ZIP was applied.
The canonical ledger and broad Python rule mirror were not changed.

### Findings and decisions

R1: The default medium/hard bands lacked canonical-size examples. The before
profile floor measured exact support 3/20 easy, 0/20 medium, 0/20 hard. Every third
raw index now uses a keyed choice of (6,6), (8,8), or (10,10), unless a dimension
is explicitly controlled. The other two thirds retain difficulty-aware geometry.
Width 6 is lawful and is now an exact axis value for every profile and placement.

R2: Both vertical half-copy rivals fit every canonical pair. Real reference-labeled
ambiguous raw lessons were retained at seed 0: easy start 0, medium start 17, hard
start 22. Default odd indices now have asymmetric row fronts. Any three consecutive
raw draws have a witness; any four have two, preserving a witness under each single
query holdout. The actual production sampler was also measured, not inferred from
this raw-draw argument. Explicit profile overrides or rejected/reordered draws are
outside the deterministic guarantee. Rivals remain finite hypotheses, not a proof
of universal identification.

R3: The selected base raw_code/target_code were whitespace-normalized rather than
byte-identical to canonical program_solution. Both fields now contain the exact
canonical text. This was an authority-text repair, not a Racket behavior change.

R4: The first repair passed geometry checks but failed three axis-provenance claims:
values had been drawn and then overwritten by the schedule. Final code chooses the
sampling domain before drawing, so recorded and pixel-observed controls agree.
Exact numeric overrides now reject booleans, strings, and fractions before int()
coercion. No silent clamping or override substitution was added.

R5: Three selected legacy tests inferred a root from source depth and failed in
the portable task-tests layout. They now use reviewer_support and public Catalog
application. Assertions and the separate frozen root fixture were preserved.

### Measured final-source checks

All 12 after-battery stages are green. Direct selected tests: 34 passed; portable
staged tests: 43 passed (25 new tests, 9 selected legacy tests, 9 frozen fixtures).
The shared override matrix accepted 55,890/55,890 draws, with zero findings or
warnings. The all-axis Cartesian probe separately accepted all 67,392 tuples,
including None/easy/medium/hard, seed 983, one global index per tuple.

The production census materialized 300 lessons (100/band, 3 demos + 1 query),
1,200 pairs, 1,166 unique inputs, zero rejections, zero ambiguity in 1,200 holdouts.
The reusable raw probe used seeds 700000..700063 and indices 0..8: 1,728 draws,
1,554 unique inputs, 1,152 overlapping four-pair windows, 4,608 holdouts, zero
measured ambiguity or hook disagreements. Independent public Racket application
matched the mirror on 64 pairs (4 canonical and 60 selected generated inputs).
Do not sum these correlated populations into an independent-trial count.

### Limits and handoff

Self-check intentionally covers a one-color contiguous row-front manifold, not
all inputs on which the broader reference executes. strict_canonical_like is that
structural predicate, not exact-size membership; the separate profile-floor gate
measures exact sizes. Preserve the broad reference on out-of-curriculum legal
recombinations. Alternate all-asymmetric and canonical-only distributions were
rejected because they would remove useful morphology or size variation.

Root review documents and checks retain the baseline, failed intermediate repair,
and final results. The two assigned audits are findings-only and leave their
sources unchanged. Visible-only solve programs and notes are separate from this
workspace; masked-query correctness and training admission were not claimed.
## Current reviewer considerations

Source SHA-256: `8f78ef0944e40e80f9b86e9d5fdb2c9515fd05240e400d097e9993c5af79bc2f`.

# Decisions — review-014044c7e991126a

## Goal and boundary

Improve the selected training-input distribution and its testability while preserving
the intended Racket mapping. Baseline `6493cddafa2f41ce449da8edec78bb1c40528c7c5a1be459371c4d089164cee3` was
read from this packet, not inferred from prior reviewer claims. The prior associated
notes GNOTE-000430..000434 and local-random-c28ce396ea35 were inspected as leads only;
no prior return ZIP was imported. Audit targets remain findings-only.

## R1 — Preserve canonical scale without losing larger problems

Before measurement: exact canonical shape/palette support easy3/20, medium0/20,
hard0/20. Width6 was not advertised even though two canonical examples require it.
Final choice: advertise width6..18; every index divisible by3 uses a keyed canonical
canvas (6,6), (8,8), or (10,10). Only unspecified dimensions use that default.
The other indices retain difficulty-aware size draws. Original rationale for the
v3 lower bound7 is not recorded; it was not assumed intentional.

Rejected: making every sample canonical-sized (unnecessary loss of scale variety),
or widening a uniform draw without a lane (probabilistic starvation can remain),
or clamping dimensions after drawing (would violate exact controls and provenance).
Measured: final exact-profile support4/20,7/20,6/20 by band; all canonical sizes also
appear in each120-draw regression census at seed101. The full matrix includes every
6x6 profile/placement combination, so width6 is real support, not a documentation edit.

## R2 — Teach row independence rather than vertical symmetry

The strongest reproduced simple rival copies one output half across the occupied
vertical span. Upper-copy and lower-copy fit every canonical pair (4/4), yet the
baseline admits all-symmetric demos followed by an asymmetric query. Twelve real
Racket outputs establish three exact witnesses; see QUESTION_ANSWER.md.

Final choice: odd raw indices force asymmetric_front, even indices retain the old
profile mixture. Three consecutive draws contain at least one witness; four contain
at least two, so any one holdout leaves a demonstration witness. The independent
canonical-size period3 yields six joint starts, all enumerated. This is why one
asymmetric example per four draws would be insufficient when query roles can rotate.

Rejected: randomly increasing the asymmetric weight (reduces but does not exclude
witness-free raw lessons), forcing every input asymmetric (unneeded loss of symmetric
morphology), and presenting two output guesses instead of sufficient demonstrations
(not a remedy for ambiguous training labels). Retain a declarative hook rather than
claiming arbitrary lessons or all possible rivals are identified.

The actual production census preserves accepted indices and reports zero rejections
in this300-lesson measurement. The raw schedule is not advertised as a theorem about
an arbitrary rejecting/resampling materializer. Explicit profile overrides can
intentionally disable the witness schedule; that is an honest exact-control contract.

## R3 — Synchronize text, not semantics

Before, selected raw/target strings were605 characters and canonical text1183;
normalization and execution parity already agreed. The current authority gate
requires exact strings. Copying the selected canonical program text into both
base fields removes textual drift without changing any executable expression.
The canonical ledger, normalized rule hash, canonical examples, and broad mirror
remain unchanged. Changing the mathematical transformation was not justified.

## R4 — Exact controls must also have exact provenance

The first repair chose a default and overwrote it to impose the schedule. The
intermediate generator `142877cf944ed59a46f096698779e9e4d6d2c229f0187a453bf6226f433ddb59` returned lawful
pixels, yet the override report correctly found three axis_provenance failures:
height27/90, width27/90, profile32/90 default metadata checks disagreed with output.
The real gen_ctx factory/drawn_store regression was added and observed failing.
Final code instead chooses singleton/default domains before drawing, leaving the
shared context as the owner of recorded axis values. A true numeric override is
never replaced by the curriculum lane. None retains the existing unset convention.

Booleans, fractional values, and strings are rejected before shared int() conversion,
so a malformed exact control raises ValueError instead of being silently converted
and later triggering a construction RuntimeError. Tests retain these failure modes.
Final matrix55,890/55,890 and Cartesian67,392/67,392 are both clear. The latter uses
one seed/index per tuple and is not a proof over all seeds.

## R5 — Make task tests portable without weakening them

The initial portable run reported3failed/36passed because three selected legacy tests
resolved ROOT by source depth, then looked for data underneath generators/TASK/.
Their assertions were valid; the inferred path was not. Selected tests now use
reviewer_support.find_root/canonical_path and public Catalog.apply, including rule
hash and purity checks. The root fixture was left unchanged. Final direct selected
suite34passed; staged suite43passed. The root suite is separately rerun and recorded;
it does not replace explicit task-local execution.

## Executable semantic contract and measurement policy

strict_canonical_like delegates to the established task-specific self_check, not a
permissive always-true hook or exact-size list. It accepts every canonical input and
structural resizings/asymmetries, while the separate profile gate counts exact scale.
The broad reference still processes legal cases outside that curriculum (including a
four-row test fixture). The row-front manifold is one color, contiguous occupied
rows with contiguous source intervals, endpoint maximum frontier, and a reflected
span that fits the canvas. These are intentional pedagogical restrictions, not
new Racket preconditions.

Declared competitors are two canonical-fitting half-copy rules and one incomplete
fill-to-axis rule. The hook consumes observed demonstration outputs and never a
query label. Survived_all is not query ambiguity. The probe iterates actual rival
registries, records canonical fit on every usable pair, counts unique inputs, and
keeps all six starts/all four holdouts. Fast mirrored labels and actual Racket labels
are explicitly separated. Passing finite rivals is not universal induction.

## Failure history and stopping decision

Retained: before battery9green/2advisory/1failed; initial regression16failed/5passed;
intermediate21passed; intermediate battery11green/1failed; staged legacy3failed/
36passed; provenance regression1failed; subsequent direct30passed then34passed;
final portable43passed; final battery12green; final production and joint probes.
Intermediate lesson census remains separately bound to its intermediate source.
The first root suite overlapped source refinement; a distinct final-source run is
used for handoff. No solve failure was fabricated: both genuine first attempts pass
visible examples, hidden labels remain withheld.

Stop after all required gates, full census, focused fresh-packet replay, two audits,
and source-bound packaging. Remaining unknowns are unseen rival programs, unusual
assembly policies, broader oracle-domain pedagogy, and hidden-query scores—not
unreported test failures or substituted source versions.

## H1 — Do not trust a no-op patch application

The first fresh extraction was nested in the review worktree. Git inherited its
parent repository and skipped all out-of-prefix hunks while returning exit0. The
independent expected-generator SHA check detected that v3 was still present and
stopped before any test could be mislabeled as a v4 pass. The original failed
helper and all receipts remain in checks/fresh_replay_before_gitinit.py and
checks/fresh-replay/. The corrected helper creates its own Git root; a second
fresh extraction applies the exact patch, has the final8f78ef...generator hash,
matches the exposed solve hash, and passes34focused tests. Do not infer a patch
was applied from a successful process return alone.

## 2026-10-23 / review-1d974aad2a9ca648

Selected source remains generator `4.0.0`, SHA-256
`8f78ef0944e40e80f9b86e9d5fdb2c9515fd05240e400d097e9993c5af79bc2f`,
with normalized rule hash `e9ecd02cbe2e`. This return does not modify the
approved generator or canonical ledger.

### Parametric-extension decision

The task-local prototype adds two episode-wide binary choices while preserving the
original row-front inference: find the occupied row span, global rightmost source
column, each interior row's frontier, and source color, then paint a right-side
interval. `fill_extent=reflected` is canonical/default and ends at the frontier
reflected across the global rightmost column; `fill_extent=to_axis` ends at that
column. `source_policy=clear` is canonical/default; `source_policy=retain` keeps
the source outline before adding the same fill. Input constraints are independent
of the setting. All four combinations are materialized as exact Racket programs.

The default `reflected-clear.rkt` is byte-identical to the canonical source
(SHA-256 `e228483658ada007f41f36b034b9aab19ff06535e4fdec54757c831d386421b5`).
The other three programs are proposed variants only. This separation was chosen
instead of changing production generation or the canonical authority because the
assignment asks for authoring evidence, not approval. Broader extent formulas,
color changes, and per-pair parameter changes were rejected as unnecessary changes
to the original reasoning pattern.

### Measured prototype evidence

`checks/parametric/66e63986855b-row-front-v1/report.json` covers seeds 0–3,
all four settings, three demonstrations and four distinct queries per episode.
It records 4/4 canonical pairs, 28/28 Python/Racket parity checks, 16/16 query
identifiability checks, 28 distinct inputs, and 116 protected-runtime Racket
evaluations. Every answer-changing declared rival is refuted by the same episode's
demonstrations before query evaluation. Four opaque public files contain only
visible demonstration pairs and query inputs.

Focused tests pass 10/10 and the complete selected-task tests pass 44/44. The
adversarial record `checks/parametric/66e63986855b-row-front-adversarial.json`
checks the bounded sampler and export transaction boundary. A duplicate-only
generator raises an explicit failure after seven attempts; duplicate visible payloads
are rejected; batch IDs are sorted; a simulated second-stage directory failure rolls
back the first install; source exports remain content-addressed; hidden
parameter/seed/query-answer mutations leave the public ID unchanged, while a
visible query-input mutation changes it.

### Limits and next action

Evidence is finite: four seeds, medium-band selected-generator inputs, two binary
parameters, and three declared rivals per setting. It does not establish universal
identifiability, production readiness, variant approval, or training admission.
The next useful action is maintainer review of whether `to_axis` and `retain` are
pedagogically desirable. Only after that decision should a separate change add any
production-facing parameter API or seek variant/training approval.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/66e63986855b/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-conflict-reconciliation:start -->
## Current proposal reconciliation

The selected row-front prototype already contains reflection_extent=1 as fill_extent=to_axis and extent=2 as reflected, plus the independent clear/retain axis. Both use the same guarded (end maxc) edit and byte-exact canonical default. Retain the four-setting selected writer and its rollback/duplicate checks; do not import a duplicate two-setting tree.

Current source-bound disposition and focused checks: [evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json). All proposed variants remain unapproved and training_admitted=false. Existing audits/failures are preserved; this reconciliation does not resolve an audit or refresh an exact-source safety approval.
<!-- arcpuzzles-current-conflict-reconciliation:end -->
