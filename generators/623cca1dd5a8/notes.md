# 623cca1dd5a8 — current generator account, v2.1.0

## Intended rule and authority

For each nonzero, same-color, four-connected component, draw the border of its
axis-aligned bounding box in the component's color on a fresh zero canvas.
Erase original interior pixels. Separate components of one color remain
separate. A two-cell-wide box has no strict interior and therefore appears
filled. The selected canonical Racket rule remains unchanged:
`RULE_HASH = 9e6a7457666e`; normalized full program SHA-256
`9e6a7457666e1f89f5d8e35e07bc47588ffab97cab0aa937cd1618f84ad6d1f8`.

## Production distribution and exact controls

The public override axes are exactly `grid_h` and `grid_w` (8..16), `n_blobs`
(2..4), and `n_distinct_colors` (2..5, including background zero). Values are
literal integers; a recognized axis set to `None` follows GenCtx's unset
convention. Unknown or retired controls and invalid seeds or indices fail
clearly. The only incompatible count pairs are `(n_blobs,
n_distinct_colors)` = `(2,4)`, `(2,5)`, and `(3,5)`. More distinct foreground
colors than components is impossible. Exact controls take precedence over
default profile preferences.

Constructive two-, three-, and four-slot partitions leave a one-cell
background moat and slots at least 3x3, so requested objects are never silently
dropped. Every shape is connected, nonrectangular, and spans its sampled box.
The ordinary constructor begins from an elbow and grows through its frontier.
The first component of every rich sample instead uses four non-corner edge
anchors connected through a keyed interior pivot; extra growth is confined to
the strict interior. This guarantees a broad component with no complete bbox
edge, while random reflections, sizes, offsets, growth, colors, and partition
cuts vary the presentation.

Default sample indices alternate a period-2 schedule. Even indices are rich
examples with repeated disconnected colors, at least one occupied strict bbox
interior, and the branched shortcut witness. Odd indices use the canonical
8x8, 9x9, or 10x10 scale, exactly two components and three total colors, with a
thin box. Difficulty affects growth and canvas support; it does not remove
canonical-scale or rich support from any band.

`EXAMPLES_NEEDED = 3`: the evaluated production lesson has three
demonstrations and one query, sampled consecutively without rejections. Every
four-pair default window contains two rich examples, so any one-pair query
holdout leaves at least one branched demonstration. The executable rivals are
color-union boxes, retaining input interiors while adding borders, filling
boxes, and a narrower visible-corner completion rule. The first, second, and
visible-corner rivals fit all three retained canonical pairs. These are four
explicit hypotheses, not an exhaustive description of all possible shortcuts.

## Accepted input domain

`self_check` accepts rectangular literal-integer ARC grids up to 30x30 with at
least one foreground component and disjoint component bboxes. It uses explicit
same-color four-connectivity. Its domain is wider than production sampling:
singletons, lines, solid rectangles, same-color diagonal contact, touching
different colors, and arbitrary connected branched shapes can be lawful when
component bboxes do not overlap. Malformed scalar values, blank or ragged
grids, and colliding bboxes are rejected. The broader lawful endpoints are
intentional, not generated curriculum promises.

## v2.1 repair: visible-corner shortcut

The accepted v2.0 source generated every component either with a thin bbox or
with two complete adjacent bbox edges. The narrower hypothesis “outline only
thin boxes or components that already expose a complete bbox corner; otherwise
leave the component unchanged” therefore produced the selected output on all
three retained canonical pairs and all 12,000 independently sampled v2.0 draws
(seeds 0..99, indices 0..39, three difficulty bands). All 29,997 sampled
components were compatible with that shortcut. A lawful broad plus shape passes
v2.0 `self_check` and refutes it. The source-bound diagnosis is retained in
`checks/623cca1dd5a8-baseline-diagnosis.json`.

v2.1 adds the branched constructor to every rich sample, declares the shortcut
as a semantic rival and canonical shortcut, and maps it to a `branched_bbox`
witness. The independent regression in `tests/test_branched_geometry.py` first
failed on eight rich and lesson-holdout cases and now passes all nine tests. The
full selected task stage passes 339 tests. A 1,536-input semantic census (512
per band) refutes the shortcut on all 256 rich draws and preserves its fit on
all 256 canonical-scale draws in each band. Fresh public Racket execution on
easy seed 0 / sample 0 matches the Python mirror and differs from the shortcut;
the complete input, output, prediction, and hashes are retained in
`counterexamples/visible-corner-completion.json` and
`checks/623cca1dd5a8-semantic-probe/report.json`.

## Earlier v2 repairs retained

The predecessor assigned a distinct color to each blob and omitted thin boxes;
v2.0 repeats colors in the rich profile and restores canonical thin-box
support. It replaced ignored or coerced overrides with the exact four-axis
contract and declared impossibilities. Palette, density, texture, and position
controls that were not observably honored remain retired. Baseline
interior-removal support was already present; the earlier repair made its
teaching support explicit rather than claiming it was absent. The retained
minimal canonical-thin, repeated-color, and occupied-interior cases remain in
`counterexamples/component-outline-regressions.json`.

## Current verification and limitations

Review `review-dd2b18fbadbea7a1` records the current source SHA-256
`ce91f28d664eaf436c90d4c29a8211f5332ff6cc9c2ef7d9bdbed8a57f940bba`.
Focused task tests pass 339/339. The full battery passes 11/12 stages: lint,
self-check execution, rule smoke, distribution, profile floor, semantic gate,
diversity, overrides, grammar, Racket lint, and authority sync are green. The
only red stage is the pre-existing generic defect-linter warning that the broad
lawful validator accepts simple shapes and rejects too few destructive
mutations. Singleton, line, and solid-rectangle inputs have meaningful rule
outputs, so this review does not narrow the domain merely to satisfy that
heuristic and does not change shared lint or approval policy.

The new branched family is still constructive rather than exhaustive: it uses
four edge anchors joined through the interior and does not teach every possible
polyomino, diagonal-connectivity decision, overlapping bbox paint order, or
interaction between touching colors. The four declared rivals are a finite
challenge set, not proof of unrestricted identifiability. Maintainer attention
is still required for the generic defect-lint policy before aggregate
acceptance.

`workspace/parametric/` is a separate runnable prototype varying outline
thickness once per episode between one and two. It is proposed, not part of the
canonical execution path or an approved training variant. Its historical
record remains below.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-a1db1ec3f4e0ce45:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `4ca87be6f5c4a5799686b2bf5e0aab5263d96f2d7d0b1625973ebae7efba5660`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit repair-bound closure of repeated-color component grouping and ignored exact controls: accepted source 25c1cceefab5831182425e74897f55dff903fdbf55240cbfdf4a8675a63f9818 introduces repeated colors, per-component semantics, canonical thin boxes, truthful exact axes and rejection of unsupported controls. tests/test_outline_semantics.py and tests/test_outline_overrides.py, checks/semantic-probe/after-v2-candidate.json and final override evidence report 330 tests, 15 actual Racket comparisons and zero override findings. This is reviewer-reported focused evidence, not automatic closure from source edits; distinct stock lint failure and adjacent-side shape restriction remain preserved.

### Assessment or prior finding

## 623cca1dd5a8

**Classification: reproduced generator shortcut plus reproduced override-contract defects; audit only, no patch made.**

The strongest rule-level shortcut is **group all cells of each color into one
object and outline the union bounding box**, instead of finding separate connected
components. It fits the generator because a 1,000-draw census found **0 examples
with a repeated blob color** (`checks/audit-oracle-probe.json`).

Exact lawful counterexample (`8 × 10`), with two disconnected color-4 L objects:

```json
[
  [0,0,0,0,0,0,0,0,0,0],
  [0,4,0,0,0,0,4,4,4,0],
  [0,4,0,0,0,0,0,0,4,0],
  [0,4,4,4,0,0,0,0,4,0],
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0]
]
```

The selected rule outlines two separate 3×3 boxes; the rival outlines one long
union box. I checked the exact input with supported `arcpuzzles apply`; it exited
0 under generator SHA-256
`4ca87be6f5c4a5799686b2bf5e0aab5263d96f2d7d0b1625973ebae7efba5660`
and rule hash `9e6a7457666e`. Input, rival, and Racket output are retained in
`checks/audit/623cca1dd5a8/`.

The generator also has concrete override defects. Seed 0 / sample 0 with
`n_blobs=4` produces only three observed color-components and is byte-identical
to default generation; `texture="warm"` is also byte-identical to default. The
defect-lint report under `checks/audits/623cca1dd5a8/` independently flags dead
or overlapping controls.

**Domain note.** Repeated-color disconnected components are outside the current
generator's output but are lawful under the selected component-based rule, so
this is a generator coverage/teaching defect rather than an invalid input claim.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-a1db1ec3f4e0ce45-v0001/audit_assets.json), manifest SHA-256 `f0e129fdeccbaa4948719fe722904691704136ecb83ced8ddc809edbfc92cede`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `ce91f28d664eaf436c90d4c29a8211f5332ff6cc9c2ef7d9bdbed8a57f940bba`.

Review `review-dd2b18fbadbea7a1` closes the source-bound adjacent-edge
restriction that remained after v2.0. The v2.1 evidence is the independent
baseline census, the keyed branched regression, the 339-test portable stage,
and a fresh Racket-checked generated refutation listed in the current account
above. This does not rewrite the retained audit disposition or claim that the
generic defect-lint policy has been resolved.

# Archived decisions — review-bb05e49bfe39011c

The remainder is the source-bound v2.0 decision record for generator SHA-256
`25c1cceefab5831182425e74897f55dff903fdbf55240cbfdf4a8675a63f9818`.
Its D6 statement that the branched constructor was not implemented is preserved
as history and superseded by the v2.1 current account above.


## Scope and outcome

The immutable draw is repair `623cca1dd5a8`, blind solve `c1b80aa665e4`, and audits
`d5178d26d905` / `a92bb76c10ef`. Only the repair task's generator, notes, new tests,
counterexamples and workspace are changed. Shared-tool proposals live under
`checks/tool-proposal/`; they are not live shared-source patches. No canonical
rule, approval field, catalog row, audit disposition or assignment was changed.

The repair is v2.0.0, generator SHA-256
`25c1cceefab5831182425e74897f55dff903fdbf55240cbfdf4a8675a63f9818`.
The predecessor SHA-256 is
`4ca87be6f5c4a5799686b2bf5e0aab5263d96f2d7d0b1625973ebae7efba5660`.
The strict aggregate remains blocked by two generic defect-linter warnings;
passing individual checks does not admit this generator to training.

## D1 / M1: components must remain distinct when they share a color

The predecessor assigned one distinct color per blob. Its original rationale is
not documented in the imported working notes. That distribution allows a learner
to group all cells of one color before drawing a box, avoiding the actual
component distinction. The retained prior audit `review-a1db1ec3f4e0ce45:v0001`
provided a lead, not a measurement of modified source. A fresh before probe found
zero repeated-color inputs in 576 draws (seeds 0..7, indices 0..23, three bands).

The default rich branch now forces a color repetition while keeping bboxes
separated. Color-union and component-union predictions disagree on an actual
Racket-checked witness. The semantic probe reads the current rival declarations
rather than maintaining a duplicate name list. It also verifies both claimed
canonical shortcuts against all three usable canonical pairs. Evidence:
`checks/semantic-probe/before-probe.json`, `after-v2-candidate.json`, and the new
task-local `counterexamples/component-outline-regressions.json`.

We rejected relying on occasional random repeated colors: finite lessons need
a distinguishing demonstration when the query separates the rules. We also
rejected one color per object as an implicit exact-control invariant.

## D2 / M2: observable exact controls with constructive feasibility

The predecessor advertised more controls than it honored. The before override
gate reproduces ignored requests; baseline regression comparisons reproduce
wrong object/color counts. v2 exposes four exact axes: height/width 8..16,
components 2..4, and total colors 2..5 including zero. Recognized `None` values
remain unset by the shared GenCtx convention. All other values must be literal
integers. Unknown, internal and retired controls raise instead of silently
falling back. This is a deliberate compatibility change and warrants v2.0.0.

The only impossible count pairs are (2,4), (2,5), and (3,5): each component uses
one foreground color and background contributes one distinct color. These
incompatibilities are declared and explicitly refused. Independently split
strips and T-shaped partitions leave at least 3x3 slots on every 8..16 canvas.
The constructor can therefore place all 2..4 requested components without a
retry cap, silent omissions, or a post-hoc override observer inventing success.

Rejected alternatives were arbitrary rejection sampling, constraining exact
requests to lucky seeds, silently clamping requested values, and advertising
palette/texture/density controls without a stable pixel-observable definition.
The retained probe checks 5,832 feasible joint draws: 81 canvases × nine feasible
count pairs × four difficulty settings × two profile parities, at seed 17.
This finite matrix is supported by the slot-size feasibility argument, not
claimed as enumeration of all seeds. The official override gate separately
records 22,230 attempts, 21,960 accepted draws, 270 declared refusals and zero
findings. Evidence: `checks/override-regression/`, `checks/code-review.md`, and
`checks/after-v2/checks/623cca1dd5a8_after_override_results.json`.

## D3 / M3: preserve canonical support while supplying rich witnesses

The baseline excluded 3x2 canonical boxes and sampled canonical profiles rarely.
Its before profile check rejected one of three canonical inputs, found only
1/60 exact profiles and 5/60 envelope profiles. The new canonical-scale branch
uses square 8, 9 or 10 canvases, two components and three total colors, including
at least one thin box. Each difficulty retains this support. Exact overrides
take precedence, so a requested 16x8 canvas does not pretend to be canonical-like.

The after profile gate accepts all three canonical inputs, records exact and
envelope support 29/60, and finds exact hits 9/20 easy, 10/20 medium, 10/20 hard.
The stricter semantic census separately observes 284/600 canonical-like draws,
above the declared 0.25 floor. These are different samples and denominators.
Evidence: before/after `*_profile_floor.json` and after `*_semantic_gate.json`.

We rejected forcing all outputs to look hollow: thin canonical boxes have no
strict interior and legitimately appear filled. We also rejected an all-rich
distribution that erases canonical support or an all-canonical distribution
that preserves the color-union shortcut.

## D4: lesson assembly and identifiability claims

The declared default schedule alternates period 2: rich at even sample indices,
canonical-scale at odd indices. The evaluated production assembly is three
demonstrations followed by one query, using consecutive accepted sample indices.
Any four-pair default window contains two rich examples; removing any one query
leaves at least one rich demonstration. Rich examples distinguish the declared
color-union, add-only/interior-preserving, and filled-box rivals. Canonical-scale
examples retain thin-box and size/color support. The statement is about default
lessons; exact overrides may intentionally remove rich witnesses.

The source-bound public census checked 100 lessons per band: 300 production
lessons, 1,200 pairs, 1,200 unique inputs and 1,200 single-query rotations, with
zero production or rotation ambiguities, materialization errors, scoring errors
or hook warnings against those three unique rivals. Fixed-seed period
enumeration checked both starts in each band: six overlapping lessons, 24 pairs
and 24 rotations, but only 11 unique inputs. Its scope is complete starts at
seed 0, not universal random support. The after battery required rotations and
consumed that exact schedule receipt. Evidence: `checks/lesson-census-v2.json`,
its summary, `checks/schedule-v2.json`, and its summary.

We rejected increasing the demonstration count without inspecting actual
assembled lessons. We also rejected treating an individual-input witness
frequency, a successful Python solve, or a finite competitor census as proof
of unrestricted induction. The exposed solve prepared three examples and two
masked queries; it is a separate workflow from the single-query census.

## D5: lawful validation and the remaining strict-lint blocker

The validator now checks every scalar, rectangularity, bounded canvas size,
same-color four-connectivity, nonempty foreground and disjoint bboxes. It accepts
a wider lawful domain than the constructor: singletons, lines, solid rectangles
and some touching-color or diagonal-contact cases. Public Racket execution
confirms the saved singleton, solid and contact endpoints, alongside canonical
and hand-made semantic cases (15/15 selected comparisons agree).

The after defect lint fails with `selfcheck-power` (7/49 destructive mutations
rejected) and `selfcheck-minimal-impostor`. Its modal-background constructions
include nonzero uniform grids and other simple shapes that are valid under this
task's fixed-zero background rule. A low refusal count alone does not show an
incorrect label or malformed input being accepted. We retained the warning and
its exact counts rather than rejecting lawful endpoints solely to make the
heuristic green. The 330 task tests include malformed-value and boundary
regressions; the public portable stage passes all 330 with zero skips.

The maintainer decision is explicit: whether to add a reviewed task-domain
calibration to the shared checker, or require a narrower production validator
as policy. This return does not grant itself a waiver. Acceptance needs attention
and the aggregate completion state remains blocked. Evidence:
`checks/after-v2/checks/623cca1dd5a8_after_defect_lint.log`,
`checks/semantic-probe/after-v2-candidate.json`, and `checks/task-tests/result.json`.

## D6 / M4: self-review of the new geometric restriction

The constructor begins with two complete adjacent bbox edges and only adds
cells before reflection. An independent review found that property in all 332
components of 144 sampled inputs. A conditional rival that outlines only such
components fits those inputs. Two separated plus shapes pass the validator,
satisfy the public axis bounds and all rich witnesses, yet separate that rival.
The saved counterexample's labels are an independent Python diagnostic, not
fresh Racket results. It is retained under `checks/override-regression/`.

The repair therefore improves the recorded defect while retaining a restricted
shape family. It does not teach arbitrary branched shapes, diagonal-connectivity
decisions or touching-color interactions. Adding a branched-shape constructor
is a concrete next sampler extension; it has not been implemented or silently
counted as part of the passing three-rival census. This limitation is separate
from the strict-linter blocker and from wrong-label claims.

## D7: proposed parametric rules

The runnable prototype chooses border thickness once per episode, from {1,2}.
Inputs are independent of the choice. Thickness 1 executes the exact canonical
program; thickness 2 draws cells whose minimum distance to a bbox edge is less
than two. Broad boxes distinguish the settings; narrow boxes alone would not.
Each demonstrated setting is held fixed over three examples and one query.

Across eight seeds and two settings, actual Racket labels support 16/16
identifiable production episodes and 64/64 query rotations. There are 70 actual
Racket labels, including both settings on three canonical inputs. Thickness 1
matches the three canonical labels exactly. Seven focused tests pass. Public
challenge files contain only demonstrations and masked query inputs, without
the seed, chosen parameter, program or query answer.

Prototype SHA-256: `f4c3e4fdcb836141ec6d51db2bfff333b3157f360e9eabf66dbc0cb3f9a47437`.
Thickness-1 program: `9e6a7457666e1f89f5d8e35e07bc47588ffab97cab0aa937cd1618f84ad6d1f8`.
Thickness-2 program: `70e37a734bdb536684516cebd31025bf24e6cc180acf0fbac85d5bd465e02932`.
Status: prototype/proposed, separately assessed and never added to the selected
canonical execution path. Evidence: `checks/parametric/run-001/report.json`,
`racket-executions.private.json`, and the exact commands in `checks/parametric/commands.json`.

## D8: reusable tooling, genuine failures and solve records

The external lesson-challenger prototype independently scores explicitly supplied
rivals over already labeled lessons. It catches the audit's omitted density-order
rival and records policy-sensitive control cases. A second optional tool compares
canonical labels with actual Racket outputs without staging a full runtime.
Both are proposals under `checks/tool-proposal/`, not shared-source modifications.
The latter's internal ArcExecutor adapter coupling is documented rather than
represented as a stable new public API. See F1..F4 in `FEEDBACK_TO_CODEX.md`.

Retained genuine failures include missing pytest before environment setup,
blocked initial package download, baseline regressions, the five failed before
battery stages, the after defect lint, a repository-layout `rule_wrap` import
failure, an audit report-key error, and temporary storage exhaustion. The audit
key was corrected to `executed_rule_hash`; its failed attempts are preserved,
and the completed rerun validates all five canonical counting labels. An initial
visual suspicion of a label error was disproved and is not reported as a defect.

Blind solve: one revision, 3/3 visible examples, earlier exposure no, reference
consulted no. Exposed repair solve: one revision, 3/3 visible examples, earlier
exposure yes, reference consulted during solve no. Both sets of masked-query
answers remain unscored/unknown to the reviewer. Notes are reviewer-authored work
logs, not token-level transcripts. No deliberately wrong solution was fabricated
as a natural failure. Tool negative controls are explicitly labeled intentional.

Final application and focused-test replay is recorded separately in
`checks/final-replay/`; exact commands, cwd, exits and retained evidence are
collected in `RESULTS.json`.
