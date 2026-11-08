# Working notes: 8e7f766c96bf

## Review review-7b55bb56b8a41740 — version 2.0.0

The selected 1.1.1 baseline emitted only target 4x4 blue frames. Its original
distribution rationale was not recorded; associated_notes.jsonl was empty.
No prior return was used as a lead. Baseline measurements, rather than prior
acceptance claims, established the defects: no contrasting shapes, ignored
palette/texture controls, misleading ranges, weak structural validation, absent
RULE_HASH, and a comment-only mismatch in the archival selected rule copy.

### Input and teaching choices

The reference still fills exactly blue components that are complete 4x4 hollow
frames. The canonical ledger is byte-identical. The selected archival target_code
was synchronized to raw_code/canonical by removing one comment; no executable
Racket behavior changed. RULE_HASH is bb4f82892380.

All generated foreground remains blue 1 on background 0, with empty interiors.
Sparse scenes contain 1..3 targets and optionally a 5x5 distractor. Contrast
scenes contain the same targets plus one each of 3x3, 4x5 and 5x4 frames. These
refute smallest-frame, small-square, height-only and width-only rivals. The
fill-all-frames rival is also checked. All four CANONICAL_SHORTCUTS actually fit
all five labeled canonical pairs; declarations are executable, not prose claims.

Sample indices alternate sparse/contrast. EXAMPLES_NEEDED=3: four consecutive
accepted samples include two contrast scenes. Any single held-out query leaves
at least one contrast demonstration. The ordinary materializer accepted all
draws in the retained 300-lesson census. Arbitrary subsets, fewer demonstrations,
forced sparse textures, and future rejection policies are not covered by that
argument; lesson_identifiable checks the actual labeled pairs against declared
rivals. No universal uniqueness or training-admission claim is made.

Sizes favor newly sampled canonical profiles while retaining broader support.
Height is 9..22, width 12..22, and target count 1..3 in every band. Easy favors
one target; hard favors two or three. Difficulty changes weights, never the
legal override domain. Blue and red are semantic colors, so obsolete warm/cool
palette controls were removed rather than treated as interchangeable colors.

### Exact support and geometric limits

The only exact controls are grid_h, grid_w, n_squares and texture=sparse|contrast.
The observer recovers each from the returned pixels. Integer axes reject bool,
float and string coercion; unknown and retired controls fail clearly. Old advertised
6..22 dimensions, six-target counts, fake palettes and negative texture branches
were not a reliable interface; this intentional contract replacement is version 2.

Packing enumerates feasible row subsets, with at least one background row/column
between shelves/objects. It randomizes partitions, shelf order, object order and
slack. No retry cap silently shortens the requested scene. A review regression
showed an optional 5x5 could exclude an otherwise feasible 9x12 three-target
sparse scene; optional configurations are now filtered before that random draw.

Shelf support is deliberately narrower than general two-dimensional placement.
Of 924 exact configurations, 888 are supported and 36 explicitly reject, with
no seed/band variance in 8,316 calls. This is not a geometric impossibility proof.
For example, a legal staggered 9x13 contrast input exists even though its exact
request is unsupported by this sampler. The witness is in the return's
checks/code-review/review.json. Expanding to a general packer was rejected as
unnecessary for the repaired lesson domain; misleading rejection wording was fixed.

The validator checks complete hollow components and empty interiors, not just
the presence of blue. It admits the canonical inputs and some legal shapes the
sampler does not draw. Foreign-colored shapes, prefilled interiors, nested frames,
no-target cases and arbitrary dense arrangements remain outside generated support.
Thus color-blind rivals are not tested by this blue-only curriculum.

### Retained verification

The return records 12/12 final battery stages, including required query rotations;
65/65 portable task tests; structural support 600/600; and canonical exact-profile
hits 10/20 easy, 14/20 medium, 11/20 hard. Its Racket-labelled census comprises
300 production lessons, 1,200 query rotations and 1,178 distinct inputs, with
no ambiguity against the five distinct declared rival rules. Full final-source
hashes, commands, observations, failed iterations and source-bound lesson data
are in RESULTS.json and checks/. A reusable joint-control probe lives in workspace/.

Self-review: random shelf/object ordering and both rectangular orientations avoid
assigning a target by position or by just one dimension. The remaining blue-only
and shelf restrictions are explicit; finite declared-rival evidence does not
certify every shortcut, unseen geometry or future lesson assembly.
## Current reviewer considerations

Source SHA-256: `f6fcc9be278a31f3860a2acca3b2cdda4ff197eff9c9a6c2166f4f25643efc77`.

# Decisions — 8e7f766c96bf / review-7b55bb56b8a41740

## Scope and evidence

The assignment was drawn once and retained. The separate blind task 9679db24667b
was solved before opening either task's generator/rule. General ARC-DESIGN.md
guidance was read with the packet instructions before the draw; it supplied no
task-specific solution. No prior return was used as a repair lead. The original
generator notes supplied no distribution rationale, so original rationale is
unknown unless inferable directly from code.

The final generator SHA-256 is
`f6fcc9be278a31f3860a2acca3b2cdda4ff197eff9c9a6c2166f4f25643efc77`.
The unchanged normalized Racket rule hash is `bb4f82892380`.

## Distribution decisions

| Choice | Reason, alternatives and limits |
|---|---|
| Add 3x3, 4x5 and 5x4 blue distractors together | The old all-target sampler could teach filling every hole. Smaller squares distinguish absolute size from relative size; rectangular distractors require both dimensions. Randomly adding just one distractor was rejected because complete lessons could omit its witness. |
| Alternate sparse and contrast samples; require three demonstrations | A four-pair contiguous lesson has two contrast scenes. Removing any one pair leaves a contrast demonstration. A longer periodic schedule was unnecessary, and independently drawing scene kinds would admit all-sparse lessons. |
| Preserve sparse scenes and optional 5x5 distractors | Retains easy and canonical-scale examples while varying target count and position. Making every scene dense would unnecessarily abandon the original visual scale. |
| Keep colors fixed at 0/1 with output 2 | These are the canonical semantic colors. The old warm/cool/varied controls had no observable effect and were removed. Other-color 4x4 frames are not generated, so color-blind rivals remain outside this review's teaching claims. |
| Height 9..22, width 12..22, targets 1..3 | These are the actual supported per-axis domains. All single values work in every band. The old wider declarations did not reliably work and are intentionally replaced in version 2.0.0. |
| Favor canonical (height,width) pairs without copying grids | New positions/layouts remain random. The final 20-draw profile check reports 10, 14 and 11 exact size/palette hits in easy, medium and hard. This is empirical support, not proof that every canonical grid is sampled. |
| Difficulty weights target counts but preserves override legality | Easy favors one; hard favors two/three. Domain truncation by difficulty caused baseline override failures and was removed. |
| Constructive randomized shelf packing | Guarantees the requested object counts within a tractable support family. The original capped placement loop could return fewer targets. Row partitions, row order, object order and spare space vary. |
| Explicit shelf incompatibilities | The full 924-setting product has 888 supported and 36 rejected settings across seeds 0,1,2 and all bands (8,316 calls). Some rejected settings have staggered legal arrangements. A general rectangle packer was not added; its absence is disclosed in the API error and retained witness. |
| Filter optional distractors before drawing | Independent review found seed-dependent failure on a feasible 9x12, three-target sparse request. Three new tests failed before this fix and pass afterward over seeds 0..19. No mandatory requested shape is dropped. |
| Structural validator | Complete blue hollow components, empty interiors, at least one target and valid integer cells replace the old 'some blue exists' test. Broader reference-lawful prefilled/foreign-color/no-target inputs are intentionally outside the sampled domain. |

## Executable rivals and exact counterexample

R1: `smallest_frame`, `height_four`, `width_four`, and `small_squares` each fit
5/5 labeled canonical pairs, verified by iterating CANONICAL_SHORTCUTS. A generated
seed-17/index-1 contrast input (11x17, one target) refutes every declared lesson
competitor under the supported Racket `apply` command. The exact input, actual
output, rival outputs and source hashes are retained under checks/question/ and
explained in QUESTION_ANSWER.md. `all_frames` is an additional lesson competitor;
it is not falsely listed as a canonical shortcut.

The final source-bound census materializes 100 lessons per band, requested starts
0..99, three demonstrations plus one query. It records all actual accepted indices,
seeds, input hashes and rejected draws; none were rejected. Production ambiguities:
0/300. Single-query rotation ambiguities: 0/1,200. Distinct inputs: 1,178. These
rotations reuse the 1,200 labeled pairs and are not 1,200 independent lessons.
The task tests additionally cover every start residue of the period-two schedule
using seeds 0 and 19, starts 0..5, in all three bands. This does not cover arbitrary
subsets, forced sparse lessons, fewer examples, or every undeclared hypothesis.

## Rule authority and curriculum

R4: the canonical ledger remains byte-identical. The archival selected target_code
had one extra comment relative to raw_code/canonical; removing that comment makes
the active sources exact matches. Baseline authority execution parity already
passed, but the required exact-source check failed; the final authority stage passes.
No intended mapping or executable Racket statement changed.

Contextual gating is present at generated-input scope: identical blue frame color
is insufficient; outer height and width jointly select the interior to paint.
The 4x5/5x4 witness distinguishes one-dimensional rivals. Multi-rule interaction,
sequential state and task-defined symbolic roles are not needed by this repair.
This annotation does not certify model mastery, training safety or corpus coverage.

## Failed attempts and process limits

The initial 1.1.1 battery failed lint, defect lint, override and authority sync;
profile and semantic stages were advisories. The initial focused suite had
52 failures and 10 passes. The first repaired source passed all 12 battery stages
and 62 tests, then independent review found the optional-distractor corner case.
Its three failing regressions and the intermediate source-bound evidence remain.
The large intermediate census is losslessly compressed with a SHA/size restoration
map in checks/archive/RESTORE.json; no failure was discarded.

The first portable task-test run and three repository tests failed because the
isolated runner disables the user-site directory containing pytest. A fresh local
virtual environment with the already installed pytest distributions resolved that
environment issue. No shared runtime source was changed. The final task stage has
65 passes; the repository suite has 417 passes and three optional torch skips.
There are no reference-test skips in the final task stage.

Both solve episodes contain one genuine submitted revision: 3/3 visible examples
pass in each, both pairs of query executions complete, and hidden-query correctness
remains unknown. Earlier rule exposure is no for the blind task and yes for the
post-repair task. Their finished work-log snapshots are preserved.

## Self-review and handoff

R2/R3: independent pixel checks and the full joint-control probe confirm counts,
shape grammar and deterministic support. Shuffling rows/objects and including both
rectangular orientations limits positional and one-dimension shortcuts; the blue-only
and shelf-only boundaries remain explicit. Final patch replay and focused tests in
a fresh original extraction are recorded separately in checks/handoff/ and RESULTS.json.

Audits A1 and A2 are findings-only and remain separate from this task's repair.
The optional Racket platform fix is a separate patch under checks/optional/; it
does not enter the selected task source delta automatically.

## Parametric review `review-417cd9039300ee73` — fixed/anchor frame dimensions

The production generator and canonical authority remain unchanged. The new
matched-input native family preserves the canonical `fixed_4x4` program exactly
and adds `anchor_dimensions`: enumerate complete hollow blue frames row-major,
retain the first frame's input-derived `(height, width)`, then fill red only the
interiors of all frames matching that pair. This is a genuine selector dependency;
the downstream eligible set cannot be chosen before the anchor dimensions exist.

The family supports 2–6 demonstrations and 1–4 independently revealable queries.
The first two demonstrations vary the anchor dimensions and include repeated
matches, explicit 4x4 frames, same-height and same-width distractors, smaller and
larger frames, and a more-frequent irrelevant dimension. They refute ten executable
rivals: all frames, anchor only, second-frame dimensions, smallest/largest,
height-only, width-only, most-frequent, fixed 3x3, and fixed 5x5. An optimized
256-seed sweep covered 512 setting jobs and 10,240 rival comparisons with no
survivor collision; all 1,024 held-out query comparisons differed across settings.
The fourth query is a 30x30 boundary-spanning scene with 12 frames and 176 blue
border cells.

Exact hashes: production generator
`f6fcc9be278a31f3860a2acca3b2cdda4ff197eff9c9a6c2166f4f25643efc77`,
canonical program
`36120aedede6912ae7db4699517eb9efa5ecab8a98c5e8a5ac7f24b825a1b0b0`,
and anchor-dimension program
`f8f1e42a3314b9cb0da21b82cf341794b2c7bbd8ae91873908930016ed361706`.
The protected audit executed 40 labels over 12 setting/prefix jobs, made 440
named-rival checks, validated 16 public projections, and found zero failures.
Native qualification passed all four setting/seed jobs. The standardized witness
changes 28 final cells when the qualified anchor pair `[6,5]` is replaced by the
fixed intermediate `[4,4]`.

Finite profiles, seeds, and named rivals do not prove universal uniqueness or
coverage of arbitrary frame grammars. Owner integration, fresh exact-source
acceptance, and any training admission remain separate and were not performed.
