# Current account: f4f11295a6f5

## Intended rule and authority

Crop the input to the smallest bounding box containing every nonzero cell. Let
that crop be a `ph × pw` pattern. The output is a `ph² × pw²` grid divided into
`ph × pw` blocks of size `ph × pw`: a nonzero selector cell emits one **exact
color-preserving copy** of the complete crop in its block, while a zero selector
cell emits a blank block.

The selected canonical Racket rule was not changed. Its pinned normalized hash
is `0a5d84c1cab4` (full normalized SHA-256
`0a5d84c1cab483b47c44e68f384e4cd5c75d644be671d6e309db39e086427623`).
The final selected generator is version `3.1.0`, SHA-256
`ca1839d9da0e1e83010e1854f91fb56def17ea6e5e974184766d396330efefb8`.

## Current decisions

- `seed` and `sample_index` now require exact Python integers; booleans,
  floats, strings and `None` are rejected, and negative sample indices are
  rejected.
- The prior version used an approximately 15% stochastic canonical-profile
  prior. Version 3.1.0 replaces that choice with a declared seven-step schedule:
  residue 0 is an exact canonical-profile draw and residues 1–6 are lawful
  multicolor general draws. This keeps canonical support near the prior rate
  (`1/7 ≈ 14.3%`) while making every four-pair lesson, and every three-demo
  query rotation of it, refute the strongest canonical-fitting color shortcut.
- Broad easy and medium draws use two crop colors; hard uses two or three.
  Pattern dimensions, the self-tile construction and the canonical default are
  unchanged.
- The semantic contract declares the rival `selector_colored_tiles`, the
  multicolor witness `multicolor_tile_copy`, and a lesson-identifiability hook.

## Minimal counterexample

`counterexamples/selector_colored_tiles.json` records a lawful 4×4 input on
which exact crop copying and selector-colored mask copying disagree. The
intended output is independently recorded by the real canonical Racket runtime
in `checks/counterexamples/f4f11295a6f5/racket.json` and covered by focused
regression tests.

## Parametric extension

`workspace/parametric/` contains an **unapproved prototype** with one
episode-level parameter, `tile_color_mode ∈ {exact, selector}`. `exact` is the
byte-identical canonical/default rule; `selector` is the nearby alternative.
Each retained episode has three demonstrations and one query, uses real Racket
labels, and distinguishes the chosen setting before the query. This prototype
is separate from the selected canonical execution path and changes no approval
or training state.

## Evidence and known limits

- Final battery: 12/12 stages green at the final generator hash.
- Final task-local regressions: 16/16 passed; parametric tests: 7/7 passed.
- Production census: 300/300 lessons and 1,200/1,200 query rotations had no
  ambiguity against the declared rival; 1,197 unique exact inputs.
- Exhaustive fixed-seed schedule census: all 21 lessons (7 starts × 3 bands)
  and all 84 rotations passed.
- These are finite checks against one declared plausible rival, not a proof of
  universal induction or uniqueness against every possible hypothesis.
- The aggregate portable `task_tests` stage remains blocked by the inherited,
  frozen root fixture `tests/test_generator_f4f11295a6f5.py`, whose fixed
  `__file__.parents[...]` canonical path does not resolve in the staged runtime.
  Packet rules forbid rewriting that fixture; the new portable test file passes.
- The prior accepted note `GNOTE-000251` was used as a design lead for the
  canonical rule, size relation and retained multicolor/nonsquare domain. Its
  historical measurements were not treated as measurements of this final source.
## Current reviewer considerations

Source SHA-256: `ca1839d9da0e1e83010e1854f91fb56def17ea6e5e974184766d396330efefb8`.

# Decisions for review-860bc30fbc4e2cec

## Scope and authority

The selected task is `f4f11295a6f5`, original ARC family `8f2ea7aa`. I treated
the canonical Racket program as binding and changed only the assigned task's
generator, new tests, notes, counterexample and separate parametric workspace.
The selected Racket rule did not change. The prior current note `GNOTE-000251`
was used as a lead for the rule interpretation, squared size relation,
multicolor/nonsquare legality and the prior approximately 15% profile policy;
its historical measurements were not reused as measurements of this source.

## F4F-01 — strict call contract

**Observed defect.** The before battery failed `defect_lint`: floats, booleans,
strings/`None` and negative sample indices could enter generation despite the
public deterministic scalar contract.

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`, and
`sample_index >= 0`. Keep the existing difficulty and axis validation.

**Alternative rejected.** Coercing integral floats/strings was rejected because
it creates aliases in the replay key space and differs from the strict contract
used by current generators.

**Probe and result.** The tests were written first and failed 15 expected cases;
after the minimal validation change all cases passed. Final task-local file:
`repo/generators/f4f11295a6f5/tests/test_review_repairs.py`.

## F4F-02 — canonical-fitting selector-color shortcut

**Observed defect.** All canonical examples are single-color. A learner can
therefore fit them with the wrong rule “copy the binary crop mask, recolored by
the selector cell” rather than exact color-preserving crop copying. On
multicolor crops this rival predicts different labels.

**Choice.** Declare the rival in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS`; add a concrete executable witness and
`lesson_identifiable`; and make the production schedule guarantee multicolor
support in every three-demo rotation.

**Input distribution choice.** Replace the prior stochastic ~15% profile draw
with a deterministic period of seven: one canonical-profile residue followed by
six multicolor general residues. This preserves approximately the same canonical
frequency (`1/7`) but gives a falsifiable curriculum guarantee. Every four
consecutive pairs contain at most one single-color profile. Therefore, after any
one pair is held out as query, at least two multicolor demonstrations remain.
Easy/medium broad draws use two colors; hard uses two or three. Pattern sizes,
densities, layouts, translation, D4 handling and exact axes remain otherwise as
before.

**Alternatives rejected.** Merely declaring the rival without changing sampling
would detect ambiguous lessons but continue producing them. Keeping an
independent random 15% profile coin was also rejected: finite average frequency
does not guarantee every lesson/window or query rotation contains a refuting
example. Making every draw multicolor was rejected because it would erase exact
single-color canonical support.

**Counterexample and checks.** The minimal saved witness is
`repo/generators/f4f11295a6f5/counterexamples/selector_colored_tiles.json`; the
canonical Racket receipt is
`checks/counterexamples/f4f11295a6f5/racket.json`. The focused tests verify that
the rival fits every canonical pair and disagrees on this witness. The 300-lesson
production census and all 1,200 held-out rotations refuted the declared rival;
a separate fixed-seed enumeration covered every one of the seven schedule starts
in all three bands (21 lessons, 84 rotations).

**Failure modes and limits.** The period is visible only through sequence order,
not through puzzle grids, but a downstream sampler that skips/reorders indices
must preserve the lesson contract or rerun the hook. The evidence is finite and
only covers declared rivals; it does not prove unique induction against arbitrary
programs. The 300-lesson census had 1,197 unique exact inputs, so three pair
collisions occurred and are not hidden by the lesson count.

## F4F-03 — parametric family extension

**Choice.** Build one small episode-level parameter,
`tile_color_mode ∈ {exact, selector}`. `exact` is the unchanged canonical rule;
`selector` instantiates the strongest nearby rival as a coherent alternative
family. The parameter is selected once per episode by seed parity. Each setting
uses three deterministic multicolor demonstrations and one query, and labels are
produced by a separately instantiated real Racket program.

**Why this parameter.** It preserves the same crop, selector, block geometry and
reasoning structure while changing one precise color-role relationship. It is
small enough for demonstrations to identify and directly exercises the ambiguity
found in F4F-02.

**Alternatives rejected.** Changing block size, rotating tiles, changing the
selector mask or composing multiple parameters would alter more than one
reasoning relation and require a larger authoring study. Those were intentionally
out of scope.

**Status and limits.** The implementation under
`repo/generators/f4f11295a6f5/workspace/parametric/` is an unapproved prototype,
not part of selected canonical execution. Both settings passed seven focused
tests and a real-Racket evidence build, but only four deterministic fixtures per
episode and two settings were evaluated.

## F4F-04 — frozen portable fixture blocker

**Observed blocker.** The official portable `task_tests` preflight fails because
the inherited frozen file
`repo/generators/f4f11295a6f5/tests/test_generator_f4f11295a6f5.py` resolves
canonical data through a fixed parent depth that is false in the staged runtime.
The assignment explicitly forbids rewriting that fixture.

**Choice.** Leave it unchanged, preserve the failure, and report overall
completion as blocked. The new test uses `reviewer_support.find_root` and
`canonical_pairs`, passes in the repository and portable layout, and is reported
separately rather than claiming an aggregate task-test pass.

## Solve records

The pre-repair blind task `60c27b9638fb` was solved from visible examples in one
revision with no earlier exposure and no reference consultation. The repaired
`f4f11295a6f5` episode was then solved from visible examples in one revision;
earlier exposure is honestly marked yes, and no reference was consulted during
the solve. Masked-query correctness remains unknown by design.

## Findings-only audits

`d172afae0ee5` and `fd24427a4ff0` were inspected and battery-tested without any
source changes. Decisions or repairs for those tasks belong to their maintainers;
see `AUDIT.md` for source-bound findings and limits.
