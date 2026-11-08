# Current notes: 42a152269589

## Rule and canonical domain

Extract four-connected monochrome polyominoes on background 0, sort by descending
area then ascending color, and pack them into 3x4 with the selected deterministic
search: translations first, then rotations, then rotations plus reflections.
There are 3..5 components, exactly three foreground colors, and twelve foreground
cells. Ordinary inputs are 10 rows by 10..13 columns. The canonical Racket rule
is unchanged; normalized RULE_HASH is `2578a5c05f72` and raw program SHA256 is
`1dd9c3e3417afbe859aa3a916a13290b9bc74d2166daa438cdfa152b596136ae`.

## Current repair: review-0865c9d4fdd1bbef, 2026-10-20

The selected baseline was `3486a8113737772c66f7b078d07ff62bc4588b17a5461349343254c8890341bf`.
Its current battery failed strict scalar validation and two false canonical
shortcut assertions. All five integer draws now use shared `draw_int_strict`,
rejecting string and float coercions while retaining valid integer/None behavior.
The generate entry point now also rejects non-integer seeds, negative or
non-integer sample indices, and difficulty values outside None/easy/medium/hard.
Negative integer seeds remain valid. Twelve golden draws before/after the final
call-argument validation change (da39b60ebee8 -> 1595b2fdf3cb), across all four
legal difficulty settings and all three slots, stayed identical.
VERSION remains 3.0.0 so valid seeded draws retain their identity.

The earlier choice to put every semantic rival into CANONICAL_SHORTCUTS was
reversed. Across all eight labeled canonical pairs, translation_only mismatches
six and one_piece_per_color mismatches two; rotation_only matches all eight.
Only rotation_only remains a canonical shortcut. All three are retained as
ordinary semantic rivals and lesson competitors. Portable tests cover strict
controls and the all-variant canonical declaration contract. The failing and
passing reproductions are retained in this return's checks/canonical-investigation.

## Ordered lesson policy and open audit

EXAMPLES_NEEDED remains 3. The sample-index schedule cycles translation_anchor,
rotation_required, reflection_and_repeat. Three consecutive demonstrations teach
all required search depths before the next query. The fixed hard-template bank
remains small; color, width, position, piece count and orientation vary. With an
explicit n_pieces=3 override, reflection remains required but repetition cannot
coexist with exactly three colors.

The prior audit `review-95c2d465e72fe468:v0001` remains open and applicable. At
seed 91999884919982, easy band, input indices 0,1,2,3, all four labels match Racket.
Demos 0,1,2 -> query3 are supported. Rotating the reflection example to query2
leaves demos 0,1,3 compatible with rotation_only, which answers that query
incorrectly. Arbitrary query rotations are unsupported; this repair does not
close that audit or claim that ordered success generalizes to rotations.

## Proposed parametric authoring extension

`workspace/parametric/prototype.py` supplies a separate proposed target_rows
parameter in {2,3}, chosen once per episode. The default3 emits the exact canonical
Racket text; 2 changes the target to 2x6 while retaining the object roles, twelve
cells, component ordering and staged dihedral packing. Complete episodes contain
three ordered demonstrations and one translation-profile query. Public files
omit parameters, seeds, reference code and private query labels.

The alternative uses connected partitions, transforms, separation and bounded
rejection to obtain mirror-classified translation/rotation/reflection witnesses.
Its labels and alternate parameter predictions are checked with actual Racket;
its inputs need not satisfy the canonical3x4 solvability validator. The shared
common-domain witness packs under both settings with different outputs. Exact
commands and finite evidence are documented in workspace/parametric/README.md
and retained checks/parametric-final/result.json (final generator bytes);
checks/parametric/result.json preserves the intermediate run. This remains a prototype, not a production API,
variant approval, or model-data admission. Query rotation and universal
identifiability are not established.

## Retained design rationale

The September29 repair replaced an invalid 2..4-piece, unique-color,
translation-only distribution with canonical3..5 component support and guaranteed
transformation witnesses. It verified the selected Racket rather than changing
its rule. Those structural choices remain. Current review measurements, source
hashes, failures, decisions and audit status belong to the current return;
historical green reports are leads, not proof for newly edited bytes.
## Current reviewer considerations

Source SHA-256: `1595b2fdf3cb839e695ebd8cd8bb783d000806c2efb08fefb2ebf94d550c92e8`.

# Decisions for review-0865c9d4fdd1bbef

## D1 — Work from the immutable draw and selected authority

The task is `42a152269589`; the original assignment, selected Racket program,
canonical ledger and audit targets are authoritative inputs. The blind task
was solved before opening generator/rule material. The parametric assessment
was developed as an authoring extension while the ordinary canonical path kept
its fixed rule. Only the selected task's allowed source surfaces changed.

The retained September 29 notes explain that an earlier sampler used 2..4
unique-color pieces and translation-only shapes, then was repaired to the
canonical 3..5 components and transformation witnesses. That rationale is
available as written history; the original author's full deliberations are
unknown. Historical green reports were treated as leads. All final acceptance
claims here use newly executed final-source evidence.

## D2 — Keep the canonical geometry, roles, and deterministic order

The ordinary rule extracts four-connected, monochrome components, orders them
by descending area then ascending color, and attempts translation packing,
rotation packing, then rotation-plus-reflection packing into a 3x4 rectangle.
Inputs retain twelve foreground cells, exactly three foreground colors, 3..5
components, background zero, and 10 rows by 10..13 columns. Those choices
preserve the selected canonical family and its exact-profile support. The
final 60-draw floor sample has 20/20 exact-profile hits in each band.

Changing the Racket output order or loosening the ordinary validator to admit
alternative rectangles was rejected: the new parameter belongs to a separate
rule family. Expanding the fixed template bank may improve diversity, but it
would change valid seeded sampling and require a dedicated coverage study.
This repair leaves that bank small and explicitly states the limitation.

## D3 — Reject coercions and invalid call arguments at the boundary

R1 reverses the original use of permissive integer draws. Shared
`GenContext.draw_int_strict` already expresses the advertised exact-integer
contract, so all five integer draws now use it. Strings, booleans and floats
cannot silently become different requests. Valid in-range integers and the
existing None sentinel remain supported. Eighteen explicit control subtests
cover type/range boundaries.

The first after-battery exposed a second layer: R2's 48 malformed seed,
sample-index and difficulty calls were still accepted. No shared public-call
validator was available in this packet, so the generator now validates these
arguments directly. Seeds may be any exact integer, including negative and
large values. Sample indices must be exact nonnegative integers. Difficulty
is None or one of easy/medium/hard. Forty-eight regression subtests cover the
reported cases, and twelve additional subtests cover documented valid calls.

Keeping permissive coercions would preserve malformed behavior at the cost
of violating the current public contract. Rejecting negative integer seeds
was also rejected because the contract permits them. VERSION stays 3.0.0:
the validation change should not perturb legal seeded draws. The retained
12-case golden comparison establishes identical outputs specifically between
the intermediate `da39b60ebee8...` and final `1595b2fdf3cb...` sources; it is
not a whole-domain proof or an original-baseline parity experiment.

## D4 — Declare only shortcuts that fit every canonical labeled pair

R3 reverses the earlier decision to copy every semantic rival into
`CANONICAL_SHORTCUTS`. A canonical shortcut is a claim about all usable
canonical examples. Across two retained variants and eight labeled pairs,
`rotation_only` fits 8/8, `translation_only` fits 2/8, and
`one_piece_per_color` fits 6/8. The latter two remain useful semantic rivals
and lesson competitors, but their canonical-shortcut labels were false.

Removing these two rivals altogether was rejected because generated
demonstrations should still distinguish them. The portable regression
iterates the actual declaration dictionary and all labeled variants rather
than hardcoding one favored canonical file. The exact rotation-only witness,
real Racket output, and final-source emission check are in
`QUESTION_ANSWER.md` and `checks/question-witness/`.

## D5 — Retain the ordered curriculum and keep the open rotation finding

The three-slot schedule supplies translation, rotation, then
reflection/repeated-color evidence. `EXAMPLES_NEEDED=3` stays unchanged.
Ordinary production uses three consecutive demonstrations followed by one
query. An explicit `n_pieces=3` override preserves the reflection requirement
but cannot repeat a color while also having three components and three colors.

The final census used the production sampler, 100 lessons per difficulty,
three demonstrations and one query, with requested starts 0..99. Exact accepted
indices and deterministic per-lesson seeds are retained. All 300 lessons
distinguish the three declared rivals. Holding out each of the four pairs
creates 1,200 overlapping diagnostic rotations; 159 are ambiguous. The
production and rotation verdicts are deliberately separate. Seven declaration
bindings are aliases of three actual rivals.

The additional final-source cyclic probe tests starts 0,1,2 at fixed seed
91999884919982 in all three bands. Eighteen unique Racket-labeled inputs form
nine ordered lessons with zero ambiguities and 36 holdouts with six
ambiguities. This covers each of the three cyclic starts at that seed without
claiming exhaustive seed support. The complete receipt is
`checks/question-witness/cyclic-starts/report.json`.

No schedule-period declaration or claim of arbitrary rotation support was
added. Existing finding `review-95c2d465e72fe468:v0001` remains open: at seed
91999884919982, the reflection input at index 2 can become an unteachable query
when indices 0,1,3 are the demonstrations. Correct per-grid labels cannot fix
missing evidence in that assembly. A future arbitrary-holdout requirement
would need additional distinguishing demonstrations, a redesigned schedule,
or verified complete-lesson rejection. Those changes exceed a boundary and
declaration repair; this return does not quietly mark them solved.

## D6 — Choose one meaningful bounded rule parameter

Two possible parameters were assessed: target rectangle geometry and permitted
transformations. The target shape was selected because both 3x4 and 2x6 use
the same twelve cells and object roles, yet can produce different valid
outputs on a shared lawful input. A transformation-permission parameter was
not added: reflection-required inputs may become unsolvable when reflections
are disabled, and distinguishing legal-domain changes would require another
complete sampling/lesson policy.

The implemented parameter is `target_rows` in the exact-integer set {2,3};
`target_cols=12//target_rows`, canonical default 3. A seeded local RNG chooses
it once per whole episode unless explicitly overridden. This is executed
geometry, not an unused flag or a recoloring of a fixed answer. Canonical
default Racket text is byte-identical. The alternative changes only OUT-H and
OUT-W declarations, guarded by the full original raw-program hash.

The canonical setting reuses existing generation with indices 0,1,2,3 at
medium difficulty. The alternative grows connected partitions of 2x6,
transforms/scatters them, and uses bounded rejection for the three solver-depth
profiles. The bound is 512 attempts per profile; exhaustion raises instead of
silently returning a weaker witness. Common component/orientation/scatter
helpers are reused. The rectangle backtracker is task-specific because the
ordinary helper is fixed to 3x4; it preserves the selected ordering.

Every episode has translation-, rotation-, and reflection-profile
demonstrations, then a translation-profile query. Python classifies solver
depth. Actual instantiated Racket verifies all labels and alternative-setting
demonstration predictions; no independent Racket depth-ablation proof is
claimed. The canonical alternative can return false on a 2x6-specific input;
such predictions are retained honestly. Alternative inputs are not presented
as passing the canonical 3x4 validator.

The CLI produced six episodes from seeds 17,29,41 with both settings, 24 actual
Racket-verified labels, and 18 alternate-rule demonstration predictions. Both
actual Racket rules also produce different outputs on a single common lawful
input. This distinguishes the finite parameter family, not all conceivable
rivals. The prototype has neither exhaustive seed coverage nor arbitrary
query-rotation evidence and remains proposed, separate from production.

## D7 — Keep public challenges independent of authoring metadata

Each public JSON contains only train input/output pairs and query inputs.
Parameters, seeds, rule programs, query labels and rival predictions are
authoring-only files. Generic episode filenames avoid encoding the parameter.
The demonstrations necessarily reveal target geometry through their outputs;
that is the intended inferential evidence, not metadata leakage.

Both visible-only solves use the supplied check/finish flow. The blind finish
records no prior exposure; the post-repair finish conservatively records the
coordinator's earlier exposure even though a separate worker used only the
visible challenge. Genuine failed revisions are kept. Query correctness is
withheld for later independent scoring, and no performance claim extends
beyond the visible demonstrations. Logs are authored summaries, not raw model
traces or probabilities.

## D8 — Preserve actual failures and build a usable return

The prototype's initial raw-versus-normalized hash mistake and missing legacy
wrapper import are retained alongside the intended red tests. The workaround
uses existing `strip_rule_wrapper` only on the pinned plain Racket lambda;
shared wrapper code was not modified. Feedback F1 identifies the general
portability defect. The initial absent pytest dependency and the audit's
unsupported medium override request remain classified as environment/probe
failures, not fabricated generator counterexamples.

Large census receipts were compressed losslessly using the included
`checks/compress_receipts.py`. It checks original and compressed identities,
verifies native-reader round trips, updates companion metadata, and removes
only a redundant raw copy after successful verification. The manifests retain
original paths, byte counts and SHA-256 values. Future runs can use the shared
CLI's existing `--gzip` option directly. Evidence bundling avoids a duplicate
repository or installed environment in the small return ZIP.

Both random audit targets are findings-only; their source hashes remain
unchanged. The final handoff applies the builder-generated patch to a fresh
runtime-closure extraction, checks every changed path/hash, and reruns the
task tests in that copy's own environment. Results and exact scope are recorded
in `RESULTS.json`; a successful patch application alone is not a test pass.

The fresh dependency closure was successfully tested through the generic
wrapper with an explicit task ID. The earlier `review.py check` convenience
shortcut failed before test execution because the undrawn closure has no
ASSIGNMENT.json. That reviewer navigation mistake and the successful
replacement command are both retained under `checks/fresh-replay`; prior draw
state and old runtime files were not copied to make the shortcut appear valid.
