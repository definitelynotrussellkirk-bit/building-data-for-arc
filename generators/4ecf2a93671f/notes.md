# Current notes: 4ecf2a93671f, v3.1.0

## Intended rule and authority

On a square input of side n, background is 0 and the sole nonzero color is paint.
The n²-by-n² output paints a cell exactly when the input cells at its block
coordinates and subcell coordinates are both zero. This is the zero-mask
Kronecker self-product. Canonical RULE_HASH remains `a7f459196d49`; this review
changes no canonical Racket program or selected authority. The existing archival
raw-code divergence is historical, not a selected execution change.

## Current input choices

- Keep the supported two-color grammar: side 3..5, paint 1..9, exact generated
  zero count 3..7. All advertised boundary combinations remain constructible.
- Keep the inherited teaching restrictions: at least three zeros and two paint
  cells; each support spans two rows and columns and is not a solid rectangle.
  These are sampling/domain restrictions, not a claim that the Racket rule is
  undefined on every excluded input. The validator can accept zero counts above
  seven on larger inputs even though the advertised generation axis stops at seven.
- Keep the four-slot size pattern 3,3,4,5. Larger inputs expose the canonical-fitting
  fixed-9×9 shortcut; three consecutive ordinary demonstrations contain a size
  witness. Difficulty changes only the larger cases' zero counts.
- Rotate the two 3×3 anchors' zero counts as (3,4), (4,5), (5,3), for a declared
  twelve-draw period. This preserves the size pattern while giving each observed
  canonical count 3,4,5 two anchors per period in every difficulty band.
- Require literal integer seed, nonnegative literal integer sample index, a
  supported difficulty or None, and literal integer exact controls or None.
  Reject malformed scalars before shared RNG coercion. None retains its default
  meaning; unknown controls and out-of-range values remain errors.

## Reversals and evidence

R1: v3.0.0 silently accepted malformed scalar controls through shared coercion.
v3.1.0 rejects them locally. The before defect lint reported 108 warnings; focused
red tests reproduced 26 malformed scalar cases. The final defect lint is green.

R2: ordinary canonical anchors previously used counts 3 and 5 and omitted the
canonical count 4. The twelve-draw rotation restores all three observed counts.
The focused regression covers one complete period in each band. The final profile
floor measures 11/20 exact canonical-profile hits in each band, 33/60 pooled.

R3: the old lesson hook rejected any unrefuted named rival, even when its answer
on the actual query was identical. The hook now rejects only query-disagreeing
survivors, while retaining malformed-demo/query checks. Canonical 3×3 lessons
are accepted; the same demonstrations followed by a 4×4 query still fail for
`fixed_side3_output`. This is a correction to the hook, not universal induction.

Task-local tests now use public portable root, canonical-data, selected-generator,
and catalog helpers. The former private `scripts` import broke collection in
the reviewer layout. No frozen root fixture or shared runtime was edited.

The exact generated 4×4 witness in `counterexamples/fixed_side3_output.json`
contains Racket output, rival output, recipe and source binding. The after
battery checks every declared witness against the selected Racket authority.
The repair return retains all before/intermediate failure evidence under checks/.

## Teaching evidence and limits

Final source: `edf751b6db95b382517a9f5434229c7b7fa0aff0740f6129235ba100831a49de`.
Use three demonstrations and one query. The production census materialized
300/300 lessons (100 per band; 1,200 pairs, 1,142 unique inputs), with zero
ambiguity against the six declared rivals and zero hook/scoring errors. Required
query rotations were clean in 1,200/1,200 cases. Enumerating twelve starts at
seed 0 across three bands covered 36 lessons and 144 rotations, also clean;
the 144 pairs contain only 29 unique inputs because windows overlap.
These are finite, source-bound checks, not all-seed, all-override or all-rival
identifiability proofs. Exact-control users assembling a new lesson policy must
check their actual assembly, particularly all-3×3 demonstrations before a larger query.

The imported associated notes remain at `evidence/associated_notes.jsonl`.
Their two-color, size-witness and structural-vs-lesson distinctions are preserved.
Maintainer intake and any required independent promotion/replay decision remain
with the maintainer; passing reviewer checks do not themselves admit training data.

## Separate proposed extension

`workspace/parametric/mask_role.py` is a task-local prototype. Its one parameter
selects background or foreground support at both scales, once per episode.
The default retains canonical behavior; exact emitted Racket supplies labels.
Public challenges omit parameters, programs and query answers. The prototype
does not alter this generator's canonical path or add a production approval.
## Current reviewer considerations

Source SHA-256: `edf751b6db95b382517a9f5434229c7b7fa0aff0740f6129235ba100831a49de`.

# Decisions for review-db1d755da47528e9

Selected task: `4ecf2a93671f`; pinned v3.0.0 → proposed v3.1.0.
Final generator SHA-256: `edf751b6db95b382517a9f5434229c7b7fa0aff0740f6129235ba100831a49de`.
Canonical RULE_HASH: `a7f459196d49`, unchanged.

## Evidence and prior rationale

The issued task's notes.md was a placeholder. I inspected the selected source,
canonical pairs, task tests and targeted retained associated notes. The five
current imported notes originate from `external-local-random:99441fc3c760`
(`review_response_external-local-random_99441fc3c760_x`). Their source records and
hashes are in `checks/prior-evidence-review.json`. The packet contains no matching
original return ZIP/hash and no current task review index or audit-disposition
ledger. No unintegrated historical patch was treated as the selected baseline.

Those notes support keeping the two-color grammar, teaching the larger-size
case, separating structural validity from lesson ambiguity, and preserving the
selected authority while retaining archival raw code. Their independent
recipient-side v13 monitor/promotion requirement remains a maintainer decision;
this review's fresh relocation and tests do not claim to close that requirement.

## D1 / R1 — Reject malformed controls before shared coercion

Prior choice: `generate` delegated scalar interpretation to shared `gen_ctx`.
The original reason for accepting coerced strings, booleans and floats is unknown.
Before defect lint produced 108 warnings. Focused regressions reproduced 26
bad scalar inputs, including boolean seeds, fractional indexes, unknown
difficulties and fractional/string exact controls.

New choice: literal integer seed; nonnegative literal integer sample index;
difficulty None or a literal supported string; each declared exact control None
or a literal integer. These checks precede RNG construction. Unknown keywords
and out-of-range integer values continue through the existing rejection paths.
None continues to mean the default; valid negative integer seeds remain allowed.

Alternative: change the shared context globally. Rejected here because it exceeds
the selected-task repair scope and could change unrelated generators. A shared
helper proposal belongs in feedback. Evidence: `checks/regressions-before.json`,
`checks/regressions-after.json`, final defect lint and override reports.

## D2 / R2 — Restore a missing canonical count without changing size support

Prior choice: ordinary canonical anchors always had 3 and 5 zeros. Canonical
inputs also contain 4 zeros. The retained evidence explains size-witness support,
but does not explain the omission of count 4.

New choice: preserve the four-slot size schedule 3,3,4,5 and rotate anchor counts
over three cycles: (3,4), (4,5), (5,3). The resulting declared period is 12.
Each full period contains six canonical-size inputs, with each observed count
appearing twice in each band. Larger defaults stay 4/5/6 zeros at side 4 and
5/6/7 zeros at side 5 for easy/medium/hard. Color continues to vary over 1..9.

Alternative: independently choose canonical count on each draw. A deterministic
rotation gives finite coverage without relying on luck and keeps the original
three-demo size witness. Alternative: enlarge only the range while retaining
the old defaults. That would leave the ordinary distribution's gap in place.

Evidence: three focused full-period tests at seed 20261019; final profile-floor
33/60 exact hits (11/20 in each band); strict-canonical 312/600; the 36-lesson
schedule census at seed 0. The v3.1.0 version is part of deterministic RNG
identity, so exact grids may change with the version even for valid old controls.

## D3 / R3 — Measure ambiguity on the actual query

Prior choice: require demonstrations to refute every declared semantic rival.
This falsely rejected the canonical 3×3 lesson because `fixed_side3_output`
agrees with its query answer. A fitting alternative is a teaching defect only
when the query asks for a distinction that the demonstrations did not teach.

New choice: validate the query, retain demo validation, and reject an unrefuted
rival only if it changes the actual query prediction. The three canonical
demonstrations plus canonical test now pass. The same demonstrations plus a
lawful generated 4×4 query still fail for `fixed_side3_output`. Malformed query
inputs remain errors. Evidence is in the focused regressions and final semantic
gate. No query output supplied by a caller is used as an authority.

## D4 — Retain bounded grammar and inherited teaching restrictions

Inputs remain square with side 3..5, background 0 and one nonzero color. The
canonical pairs do not establish a multicolor selection or tie rule, so I did
not expand that grammar. The output therefore stays within 25×25.

Advertised exact controls remain side 3..5, paint 1..9, generated zero count 3..7.
The inherited validator requires at least three zeros, at least two paint cells,
and each support to span two rows/columns and not be a solid rectangle. These
restrictions rule out simple mask degeneracies but narrow the distribution;
their necessity over the full reference-lawful domain has not been proved.
The validator is broader than generated count support on larger inputs: it does
not impose an upper bound of seven zeros. This distinction is intentional here.

Rejection sampling remains deterministic and capped at 256 attempts, preserving
every requested exact axis. The battery found no override incompatibility or
generation crash in its tested cases. I did not claim exhaustive joint coverage
for every seed or expand to rectangular, multicolor, all-zero or single-color
inputs merely because the Racket program might execute them.

## D5 — Teaching policy, census and new-shortcut review

The evaluated policy is three demonstrations and one query from the production
sampler, with arbitrary query rotation required among each materialized group
of four. The size pattern guarantees that any three consecutive ordinary draws
include a non-3×3 example. Holding out one of a four-draw group still leaves a
larger example in the demonstrations. This reasoning concerns the ordinary
schedule; a caller overriding every side to 3 and then requesting a larger query
must separately check that assembly.

The larger census used 100 lessons per band: 300/300 materialized, 1,200 pairs,
1,142 unique inputs, zero production ambiguity/hook/scoring errors, and zero
ambiguity/hook/scoring errors in 1,200 query rotations. An additional enumeration
covered all 12 declared starts at seed 0 in all three bands: 36 lessons, 144
rotations, 144 pairs but only 29 unique inputs because windows overlap. All
declared-rival checks were clean. Exact seeds/starts and source binding are in
`checks/lesson-census.json` and `checks/schedule-census.json`.

The six declared rivals cover block-only, subcell-only, OR, foreground-mask,
count-only and fixed-size mistakes. The last fits all four canonical pairs;
the exact 4×4 witness is in the task's `counterexamples/fixed_side3_output.json`.
The count rotation does not add a fixed foreground color or remove any size
witness. It remains a predictable schedule, so finite declared-rival success is
not evidence against every possible position-based or memorization strategy.
The fixed-seed enumeration establishes neither the period's universality nor
all-seed identifiability, and these records do not admit solver trajectories.

## D6 / R4 — Make task tests portable using the public API

The inherited task-local test imported private `scripts` code and a private
per-puzzle alias and guessed a root by parent depth. Its collection failed in
the reviewer layout before test execution. Replaced those lookups with
`reviewer_support.find_root`, `canonical_pairs`, `load_selected_generator` and
public catalog/authority mappings. The frozen root fixture is unchanged.
Evidence: `checks/test-portability-before.json` and the final task-tests receipt.

## D7 / P1 — A suitable one-parameter prototype

Status: **prototype/proposed**, separate from the canonical repair.
Implementation: `repo/generators/4ecf2a93671f/workspace/parametric/mask_role.py`.
The parameter `mask_role` is either `background` (default) or `foreground`, and
selects the same predicate at block and subcell coordinates. It changes the
executed transformation while preserving the self-product reasoning. A second
parameter was unnecessary; varying input color alone would duplicate an input
axis rather than introduce a meaningful rule parameter.

The role is fixed once per episode. Explicit settings are supported; None uses
seed modulo two before any pair draw. Both settings use identical inputs at the
same seed, have the same lawful grammar, and emit exact self-contained Racket
lambdas. All labels and finite-setting rival predictions execute through
`RacketBridge`; no Python output mirror supplies prototype labels.

Evidence in `checks/parametric/`: seed 46371, two complete 3-demo/1-query episodes,
all eight labels reexecuted, both settings identified by demonstrations, default
parity on four canonical and four generated pairs. A lawful 3×3 witness yields
16 versus 25 painted cells. Public challenges contain only demonstrations and
query inputs. The two Racket hashes are:

- background: `88ae3b60304ac1c73900e72d0aa1a6c9730f807ce28f5aceeaf1b70b16662a03`
- foreground: `44af0f9cb8c4fb9952e5b3cf41381d852888687e704108808c742eba5a2e33dc`

The 11 prototype tests cover exact execution, canonical parity, setting selection,
replay, finite ambiguity, public schema and invalid bounds. Development failures
are retained, including a corrected replay-seed record and a Racket startup
timeout. The unchanged code passed sequential retries. This is bounded evidence
for two settings and selected seeds, not a production parametric API or approval.

## D8 — Work within storage limits while retaining source verification

The original archive contains 76,576 files and about 1.10 GB expanded data. A full
extraction actually failed with ENOSPC. The working tree therefore materializes
the required public/runtime closure and complete assigned task homes. The new
stdlib `checks/tooling/packet_zip.py` streams every original member and verifies
the exact inventory/hashes; the original archive receipt is retained. An existing
different destination file is never overwritten by selective extraction.

The unmodified stock package command then failed on a missing unrelated immutable
source (`repo/REVIEW/README.md`), recorded in `checks/stock-package-diagnostic.json`.
The optional archive-backed builder verifies existing local immutable files and
uses verified original archive bytes only for absent immutable files. Editable
sources, frozen baselines, scope checks, budgets, stock INTAKE generation and
return validation remain under issued logic. The one version-pinned disposable
AST transformation is included as a non-applied proposal. No shared source file
was edited. All 38 tool tests passed with zero skips, including synthetic
byte-for-byte stock return/INTAKE parity and rejection cases.

This packaging route requires explicit maintainer attention and is not described
as a successful stock `review.py package` run. The final handoff uses the stock
fresh-replay command with `--runtime-closure`; its extraction is partial and its
focused tests run in the fresh checkout's own environment. The replay receipt
and final patch identity record provide the exact tested-source boundary.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-8a556b3bdc6ddb5e:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `edf751b6db95b382517a9f5434229c7b7fa0aff0740f6129235ba100831a49de`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported on unchanged source edf751b6db95b382517a9f5434229c7b7fa0aff0740f6129235ba100831a49de. No issue in finite checked scope:55tasktests,explicitperiod12strictsemanticpass312/600strict,12lessons/48rotationsclean,36fixedseedresidue-lessons/144rotations. Earliercombinedcontrollerinterruptednotpass. Noapprovalupgrade orclosureofotherfindings. Retain source-bound evidence: `checks/audit/4ecf2a93671f-combined/RUNTIME_MANIFEST.json` `checks/audit/4ecf2a93671f-combined/checks/4ecf2a93671f_audit_battery_summary.json` `checks/audit/4ecf2a93671f-combined/checks/4ecf2a93671f_audit_commands.jsonl` `checks/audit/4ecf2a93671f-combined/checks/4ecf2a93671f_audit_semantic_gate.json` `checks/audit/4ecf2a93671f-combined/checks/4ecf2a93671f_audit_semantic_gate.log` `checks/audit/4ecf2a93671f-combined/checks/4ecf2a93671f_audit_semantic_gate.receipt` `checks/audit/4ecf2a93671f-combined/checks/4ecf2a93671f_audit_summary.json` `checks/audit/4ecf2a93671f-combined/checks/task_tests.xml` `checks/audit/4ecf2a93671f-combined/progress.log` `checks/audit/4ecf2a93671f-combined/result.json` `checks/audit/4ecf2a93671f-semantic-enumerated/RUNTIME_MANIFEST.json` `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_battery_summary.json` `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_commands.jsonl` `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_semantic_gate.json` `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_semantic_gate.log` `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_semantic_gate.ok` `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_semantic_gate.receipt` `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_semantic_gate.schedule-census.json` `checks/audit/4ecf2a93671f-semantic-enumerated/progress.log` `checks/audit/4ecf2a93671f-semantic-enumerated/result.json`

### Assessment or prior finding

## 4ecf2a93671f

**Conclusion: No issue found in checked scope.** Audited source SHA-256 `edf751b6db95b382517a9f5434229c7b7fa0aff0740f6129235ba100831a49de`; source left unchanged.

The combined audit's portable task-test stage completed with 55 passing tests (`checks/audit/4ecf2a93671f-combined/checks/task_tests.xml`). Its controller was interrupted while entering the semantic stage, so that aggregate is retained as incomplete rather than called a pass: `checks/audit/4ecf2a93671f-combined/result.json`.

I reran the strict semantic gate with the declared 12-slot schedule period enumerated. It passed with strict canonical support 312/600 (52%), all 12/12 smoke lessons identifiable, and 0/48 supported query rotations ambiguous. The fixed-seed schedule census executed 36 residue/band lessons and 144 rotations against the declared rivals. It exercised six semantic witnesses, including block/subcell conditions, AND-vs-OR, spatial arrangement, color role, and output-size scaling. Evidence: `checks/audit/4ecf2a93671f-semantic-enumerated/checks/4ecf2a93671f_audit_semantic_gate.json` and its schedule-census receipt.

Scope limit: this is finite source-bound checking of the generator's declared rivals and tests, not universal proof or approval.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
