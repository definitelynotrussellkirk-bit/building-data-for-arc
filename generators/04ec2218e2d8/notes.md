# Current notes: 04ec2218e2d8

## Intended rule

Find each 4-connected cyan (`8`) component. Use that component's bounding box to
compute an inset of `max(2, min(height, width) // 4)`. Recolor **only cyan object
cells**: the inset center becomes yellow (`4`); the remaining top-left,
top-right, bottom-left, and bottom-right bbox regions become magenta (`6`), blue
(`1`), red (`2`), and green (`3`). Non-object cells inside a component's
bounding box remain unchanged.

`RULE_HASH = 6d0c8228b329` remains pinned to the unchanged canonical Racket
authority. The three canonical inputs and labels remain positive controls.

## Current generated manifold

- 23×23 black canvas.
- Exactly two or three separated, 4-connected cyan components.
- Every component has a 6..14 by 6..14 bounding box inside a one-cell canvas
  border.
- `scene_profile` controls the normalized bbox-size tuple: three demonstrated
  profiles plus two generalized profiles.
- `component_style` is exact and observable: `solid`, `interior_hole`, or
  `edge_notch`. Every component in one scene uses the same style. A non-solid
  component has exactly one missing cell; an interior hole is strictly inside
  the bbox and an edge notch is on exactly one non-corner bbox edge.
- A fixed period-3 schedule cycles all component styles by `sample_index`. Every
  three consecutive examples therefore include both non-solid styles.
- Positions, rectangle orientations, cutout positions, packing, and whole-scene
  D4 transforms are nuisance variables. Literal canonical-input rehearsal is a
  bounded 1-in-10 branch on solid demonstrated profiles only.

## Decision reversal and evidence

Version 3.0.0 intentionally accepted/generated only solid rectangles. Two
retained source-bound reviews (`review-d989bddd1e8298ce:v0001` and
`review-72d07f8d7ac14001:v0001`) independently found that this made the plausible
rival “paint the whole bounding box” indistinguishable from the intended
object-cell rule on all generated lessons. The prior choice is reversed in
version 4.0.0 because the selected authority explicitly preserves non-object
cells inside a component bbox.

The retained minimum-area generated witness is
`counterexamples/semantic-shortcuts/bbox_fill_minimal.json`; its reproducer is
`counterexamples/semantic-shortcuts/reproduce.py`. It has two 6×6 bboxes (the
minimum possible total bbox area, 72) with one edge notch each. Canonical Racket
leaves both notches `0`; the bbox-fill rival paints both blue (`1`). The exact
Racket hash and generator source hash are embedded in the witness.

Focused staged tests cover all 15 scene/style combinations in every difficulty
band, strict scalar rejection, topology rejection, canonical controls, rival
fit/disagreement, and all four query rotations for every schedule residue. The
fixed-seed period census materialized 9 lessons and 36 rotations with no declared
rival ambiguity. These are finite checks against one named rival, not a proof of
unique induction over all possible rules.

## Assumptions and limits

- All components in a generated scene share one topology style; mixed-style
  scenes are deliberately outside this calibrated grammar.
- Only one missing cell per component is admitted. Multiple holes, corner
  cutouts, disconnected shapes, and bbox-shrinking cuts are rejected.
- The Python mirror is broad over arbitrary cyan components, while `self_check`
  is intentionally narrow and distribution-facing.
- Difficulty changes profile weights but not the rule. It does not currently
  create a monotone reasoning-complexity ladder.
- Named rival coverage is bounded. Other shortcuts may remain; future audits
  should look especially for formulas tied to fixed canvas size, component count,
  shared style, or the restricted one-cutout topology.
## Current reviewer considerations

Source SHA-256: `705979abafe1f0f810601ed2e37f98b635b7a7c873b2fb8105790711847b52f5`.

# 04ec2218e2d8 Repair Decisions and Implementation Plan

> Execution method: native implementation in this review workspace, following
> test-first changes and the packet's required verification/package workflow.

**Goal:** remove the strict-scalar defect and make generated lessons distinguish
cell-only recoloring from the strongest canonical-fitting bounding-box-fill rival.

**Architecture:** preserve the canonical Racket rule and the existing 23×23,
two/three-object size grammar. Extend each rectangular bounding box with an exact,
observable `component_style` axis (`solid`, `interior_hole`, `edge_notch`); default
sample-index scheduling guarantees every three consecutive examples contain
non-solid evidence. Add deterministic semantic rivals, witnesses, and a lesson
hook bound to the same Python mirror used by tests.

**Spec:** `WORK/DUTIES.md`, `WORK/ARC-DESIGN.md`, and the two retained findings in
`repo/generators/04ec2218e2d8/evidence/review_index.json`.

## Global constraints

- Edit only `repo/generators/04ec2218e2d8/` plus required review artifacts.
- Keep `RULE_HASH = 6d0c8228b329` and canonical Racket sources unchanged unless
  evidence proves an authority defect; current evidence does not.
- Preserve all three canonical inputs and outputs exactly.
- Keep generated cyan components 4-connected, bbox-stable, separated, and inside
  the existing one-cell canvas border.
- Reject Boolean/coerced/negative `sample_index` values rather than relying on
  permissive `GenCtx` construction.
- Treat finite named-rival results as evidence, not universal identifiability.

## Review focus

1. Bad scalar controls: bool, float, string, and negative `sample_index` must fail.
2. Topology mutations must not disconnect a cyan component or shrink its bbox.
3. Exact overrides must be recoverable for every scene/style combination.
4. Every three-example schedule window and every one-query rotation must retain a
   non-solid demonstration that refutes bbox fill.
5. Literal public rehearsal must remain bounded and only occur for `solid` style.

## Task 1 — strict control validation

- [x] Add focused tests that reproduce the five `defect_lint` warnings.
- [x] Verify the tests fail against version 3.0.0.
- [x] Validate `seed` and nonnegative exact-int `sample_index` at the generator
      boundary; bump the generator version.
- [x] Run the focused tests and standalone defect lint.

## Task 2 — lawful non-solid component distribution

- [x] Add failing tests for the three exact component styles, observable overrides,
      bbox stability, connectivity, and invalid mixed/multi-cutout scenes.
- [x] Add `component_style` to `AXES` and introduce a three-slot deterministic
      schedule.
- [x] Apply one deterministic interior hole or non-corner edge notch per component
      after packing and before whole-scene D4 transformation.
- [x] Extend scene analysis/self-check to recognize only the three declared styles.
- [x] Preserve literal public inputs only on solid-style draws.

## Task 3 — semantic teaching contract

- [x] Add a failing test showing bbox fill fits all canonical pairs but differs on a
      generated non-solid witness.
- [x] Declare strict-manifold, rival, witness, schedule, and lesson-identifiability
      hooks.
- [x] Exhaustively test every residue of the three-slot schedule, including all
      four query rotations from a 3-demo+1-query lesson.
- [x] Save one minimal generated counterexample with canonical and rival outputs.

## Task 4 — evidence, solve, audits, and return

- [x] Run focused tests, task-test staging, after battery, and a 100-lesson-per-band
      rotating census.
- [x] Complete the required post-repair visible-only solve without consulting source.
- [x] Perform both findings-only audit assignments and retain reproductions.
- [x] Update notes, question answer, review summary, feedback, and `RESULTS.json`.
- [x] Replay/package through the packet packager and inspect the returned ZIP.

## Alternatives considered

- **Document solid rectangles as the entire domain.** Rejected for this repair:
  both retained audits identify the resulting bbox-fill shortcut, and the selected
  authority explicitly preserves holes/non-object cells.
- **Change the Racket rule to paint bboxes.** Rejected: it would alter canonical
  semantics and erase the authority's cell-only behavior without evidence of a rule
  bug.
- **Randomly add holes without a schedule or semantic contract.** Rejected: aggregate
  diversity would not ensure each three-demonstration lesson distinguishes the rival.

## Execution ledger

- Pre-flight: this packet is not a Git checkout; the extracted, hash-verified review
  workspace is the isolated implementation surface. Creating a nested worktree would
  bypass the journal and patch builder.
- Task 1 root cause: `generate()` forwarded seed and sample index directly to the
  permissive context constructor, so Boolean, float, string, and negative controls
  were accepted before any generator validation.
- Task 1 RED: staged `task_tests` reported 9 expected subtest failures in
  `test_rejects_invalid_scalar_controls`; all other 9 tests passed.
- Task 1 GREEN: staged `task_tests` passed 9 tests plus 9 subtests; standalone
  `defect_lint` passed with no warnings.
- Ruling: use `VERSION = "4.0.0"` now rather than an intermediate 3.1 release because
  Tasks 2–3 deliberately expand the observable generation domain and axes. Cost if
  wrong: deterministic sample identities change one release earlier inside this same
  unshipped repair packet.
- Task 2 RED: staged `task_tests` failed on the absent `component_style` axis,
  schedule declarations, non-solid override, and observability; unrelated tests stayed
  green.
- Task 2 GREEN: all 10 staged tests plus 9 scalar subtests passed. Every declared
  scene/style combination is constructive in all bands; each non-solid component has
  exactly one bbox-stable cutout; mixed, corner, and multi-cutout scenes are rejected.
- Task 2 authority check: `rule_smoke` passed after non-solid generation was enabled,
  confirming the unchanged Racket authority agrees with the Python mirror on the
  sampled hole/notch inputs.
- Ruling: use a 1-in-10 literal-public branch only for `solid` draws. The previous
  1-in-20 rate would fall below the retained rehearsal floor after two-thirds of
  default samples became non-solid. Cost if wrong: published-layout rehearsal is
  modestly more frequent among solid examples, without changing rule coverage.
- Task 3 RED: four staged tests failed only because semantic rivals, witnesses,
  strict-manifold, and lesson-identifiability hooks were absent; all construction and
  authority tests remained green.
- Task 3 GREEN: all 14 staged tests plus 9 scalar subtests passed. The bbox-fill
  rival matches all three public pairs and differs on both generated non-solid styles.
- Task 3 semantic evidence: strict gate measured 600/600 accepted draws, all three
  witnesses firing across every band, 2/2 rival claims verified, 12/12 lessons
  identifiable, and 0/48 ambiguous rotations. Its sole warning requested fixed-seed
  schedule enumeration; the follow-up period census completed all 9 residue/band
  lessons and all 36 query rotations with zero ambiguity or hook/scoring errors.
- Task 3 counterexample: retained the minimum declared bbox-area witness (two 6x6
  boxes, total area 72) with exact canonical Racket and rival outputs plus a portable
  reproducer.
- Ruling: keep the semantic-gate schedule-enumeration warning as procedural evidence
  rather than deleting `LESSON_SCHEDULE_PERIOD` to obtain a cosmetic green verdict.
  The separate source-bound census performs the requested enumeration. Cost if wrong:
  maintainers must consult two receipts instead of one aggregate status.

- Task 4 final lesson evidence: the production census materialized 300/300 lessons
  (100 per band), 1,200 labeled pairs and 1,200 required query rotations, with
  zero declared-rival ambiguity, hook warnings, scoring errors, or materialization
  errors; 1,191 inputs were unique.
- Ruling: losslessly gzip the 29,857,916-byte census with a manifest, verified
  restoration helper, and external raw backup rather than truncate rows to meet
  the 25 MiB return budget. Cost if wrong: maintainers must run one documented
  restore command before reading the raw JSON directly.
- Audit `1569ecfa4ff1`: no issue found after 6 portable tests and a strict semantic
  PASS (600/600 strict draws, 5 witnesses, 12/12 lessons, 0/36 ambiguous rotations).
- Audit `346480121fcb`: retained a concrete key-ignoring teaching shortcut (4/4
  easy key=1 Racket labels matched; 0/1 legal hard key=2 label matched) and override
  contract evidence (47,880 draws, 5,332 findings, unknown-key acceptance). The
  audit target remains unchanged as required.
- Self-review: the repair defeats whole-bbox filling but deliberately keeps one
  shared style and at most one cutout per component. A rival specialized to that
  narrow manifold could remain observationally equivalent; the evidence is finite
  declared-rival coverage, not universal induction.
- Task 4 fresh replay: extracted the original packet anew, verified the provisional
  `source.patch` with `git apply --check`, applied it, matched all six patched files
  byte-for-byte to the implementation workspace, reproduced generator SHA-256
  `705979abafe1f0f810601ed2e37f98b635b7a7c873b2fb8105790711847b52f5`, and
  passed 14 task tests plus 9 subtests. The standalone bbox-fill reproducer also
  returned the exact two expected disagreement cells.

## 2026-10-21 parametric-extension review

This assignment left the selected version 4.0.0 generator and canonical authority
unchanged. The before battery passed all 12 stages on source SHA-256
`705979abafe1f0f810601ed2e37f98b635b7a7c873b2fb8105790711847b52f5`; no
new canonical-distribution defect justified reopening the approved repair.

A separate proposed prototype now lives in `workspace/parametric/`. It varies one
hidden episode-level parameter, `inset_divisor`, over `{4, 3}` while preserving
the original object detection, per-object bbox, cell-only painting, yellow center,
and four quadrant roles. Divisor 4 is the exact canonical program (SHA-256
`ab179edbdbc9bce0fe184c4e071d6880e6c011eaa22047f4ede40af402fda075`,
normalized hash `6d0c8228b329`); divisor 3 changes only that literal (SHA-256
`80991f655954e1a26f06f576c7f2814e983d10534afe36e00b622269a8832c17`,
normalized hash `209457a35cb8`).

The parameter is selected once per episode. Controlled selected-generator inputs
ensure at least one component has minimum bbox side at least 9, because sides 6–8
make both settings collapse to inset 2. Two complete retained episodes, exact
Racket programs, masked public challenges, canonical replay, and a 24-cell shared
setting witness are under `checks/parametric/inset-gallery/`. Focused tests are in
`tests/test_parametric_inset.py`. This is finite prototype evidence only; it does
not modify production APIs, approval, or training admission.

The ledger has two task rows with identical program bytes. Prototype loading now
requires one unique nonempty program across all variants rather than exactly one
row, rejecting actual divergence while preserving the canonical text.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-72d07f8d7ac14001:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ccc77c6aa3a51d2eca67b6094795c13db2df49c71802aeb63fa354b844401f88`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve old solid-rectangle-only bbox-fill support finding against current705979ab v4.0.0 source. Existing repair admits lawful interior_hole andedge_notch components andperiod3style scheduling. Retained generated minimum-area edge-notch witness has72total bbox area:canonical Racket preserves zeros wherebbox-fill paintsblue. Current reviewer reports300lessons/1200rotations clean,29 portable tests and6 prototype tests repeated in full fresh replay,12/12 schedule-enumerated battery. No production source edit this intake;finite named-rival evidence,not universal identification.

### Assessment or prior finding

## 04ec2218e2d8

**Reproduced possible shortcut / domain question (source left unchanged).**
Current audited `generator.py` SHA-256 is
`ccc77c6aa3a51d2eca67b6094795c13db2df49c71802aeb63fa354b844401f88`.
The authority recolors only cyan component cells, but the accepted/generated
domain permits only solid cyan rectangles. A rival that paints every cell of
each component's bounding box is therefore observationally identical on the
current distribution.

An independent current-source probe generated 1,500 cases (100 seeds × five
profiles × three difficulty bands). Every component was bbox-solid and the
bbox-fill rival matched `rule_mirror` on 1,500/1,500 cases. On a 23×23 scene
with an 8×8 cyan block at `(2,2)`, a 6×6 block at `(14,14)`, and a black hole at
`(5,5)`, the supported Racket rule leaves the hole `0`; the bbox-fill rival
paints it yellow `4`. `self_check` rejects the holed input, so no current lesson
can distinguish the broader cell-only rule from bbox painting.

Evidence:

- `checks/audit/04ec2218e2d8/input.json` and `racket.json` — exact holed input and
  supported authority output, rule hash `6d0c8228b329`;
- `checks/audit/04ec2218e2d8/probe.py`, `probe.log`, and `probe.json` — 1,500-case
  distribution probe plus authority/rival counterexample.

This is a **domain question**, not a demonstrated wrong label: if solid
rectangles are the intended manifold, the rival is equivalent there. If the
broader authority is meant to be learned, admit lawful non-solid cyan components
or narrow/document the authority. I did not edit this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-72d07f8d7ac14001-v0001/audit_assets.json), manifest SHA-256 `cdc2a5d2d8bda4f274aa25033304fdc935e85bbb6d6b4425410b7f812a108c57`.
<!-- arcpuzzles-current-audit-assessment:end -->
