# Current notes: `6d678fbbe87e`

## Intended rule

Inspect every 2x2 window in the original input.  If exactly three cells have one
equal nonzero color and the fourth cell is zero, fill that zero with the shared
color.  Apply all qualifying fills simultaneously and preserve every other cell.
The selected canonical authority is unchanged and pinned by
`RULE_HASH = "e0165fc03ab4"`.

## Current generator (`3.0.0`)

- Public exact controls: `grid_h` in `4..8`, `grid_w` in `5..10`; both are
  recoverable from pixels.  Unknown, coercive, or malformed arguments are
  rejected.
- Lawful generated inputs use exactly three nonzero colors and three or four
  nonconflicting qualifying windows, with every color participating.
- Four deterministic schedule profiles are used: one isolated canonical anchor
  and three connected multi-window profiles.
- Three demonstrations plus one query are required.  The lesson hook refutes
  four declared canonical-fitting rivals under all allowed query rotations:
  isolated-L-only, component-bounding-box, one-completion-per-color, and
  iterative fixed-point closure.
- Difficulty changes broad-profile default size/orientation support, but every
  explicit legal size override remains available in every band.

## Reversed prior decision

Version 2.1 intentionally emitted only isolated three-cell L components and
advertised a broad nine-axis surface.  That choice was reversed because retained
review `review-20b3349acd859fe9:v0001` and the assigned baseline showed that
object-level shortcuts fit all canonical and generated examples, while several
axes were ignored or coerced.  The current connected witness and strict two-axis
API directly address those failures.

## Evidence

- focused portable suite: 104 passed (`checks/task-tests-final/result.json`);
- final battery: 12/12 green
  (`checks/after-with-schedule/checks/6d678fbbe87e_after_battery_summary.json`);
- complete declared period at fixed seed 0: 12 lessons / 48 rotations, zero
  findings (`checks/schedule-period-s0.summary.json`);
- broad census: 300 lessons / 1,200 query rotations / 1,171 unique inputs, zero
  ambiguity, hook, materialization, or scoring findings
  (`checks/lesson-census-final.summary.json`); and
- minimal connected counterexample:
  `counterexamples/review-29dec646310b6c97-v0001/curriculum-witness.json`.

## Known limits / open findings

The accepted grammar is intentionally narrower than the full mathematical domain
of the authority.  Rival and census evidence is finite: it does not prove unique
induction against every possible hypothesis, and the exhaustive schedule receipt
covers every declared residue only at fixed seed 0.  Other seeds, new rival
families, or a downstream change to the three-demo/one-query rotation policy need
new source-bound evidence.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-20b3349acd859fe9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7e907ba3ea4982c5d8787176f083b8caf11202d7ecd9a68e3c8f7c7a4f6e528c`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Repair adds connected multi-window curriculum witnesses and explicit component/bbox rivals, addressing exact prior separated-three-cell-L support shortcut. Reported104tests,300lessons/1200rotations and fixed-period receipt; explicit reviewer-reported disposition required. Exact repaired generator=659439eb5d5c14675a0b054b9a7cb04b7d4ff0c6294c1abb1cfbd14d02980f8e. Evidence=/home/user/Desktop/ARCpuzzles/var/review/new-return-tools-review/tool-disposition-proposals-nine.json sha256=76a7ea73fa5513ccc75ba5c5d6aad9abc549b59dfa65563ac320261676fd2870. Maintainer explicitly resolves this prior source-bound finding on accepted reviewer-reported repair; no independent rerun or universal correctness claim.

### Assessment or prior finding

## 6d678fbbe87e

**Plausible component-box shortcut survives canonical and default generation; no fix included.** Source reviewed: SHA-256 `7e907ba3ea4982c5d8787176f083b8caf11202d7ecd9a68e3c8f7c7a4f6e528c`. Executed rule hash: `e0165fc03ab4`.

Shortcut: for every four-connected monochrome component with exactly three cells and a 2×2 bounding box, fill the missing bounding-box corner. This fits all three labeled canonical pairs. It also matched an independent window-rule mirror on all 300 sampled defaults (100 per band, seed base `66780000`); all 300 passed `self_check`, all 300 consisted only of the shortcut's isolated three-cell component form, and there were 284 unique inputs.

Exact accepted-domain disagreement input:

```json
[
  [4,4,0,0],
  [4,0,0,0],
  [4,0,0,0],
  [0,0,0,0]
]
```

The top-left 2×2 window contains exactly three 4s and one zero, so the Racket authority fills `(1,1)` with 4. The shortcut sees one four-cell connected component rather than an isolated three-cell L and leaves the grid unchanged. The input passes the target's `self_check` with no errors, but it is outside the generator's documented default domain because the ordinary sampler deliberately places separated three-cell partial blocks.

Evidence and exact commands:

- `checks/audit/6d678fbbe87e/input.json`
- `checks/audit/6d678fbbe87e/racket.json`
- `checks/audit/6d678fbbe87e/rival.json`
- `checks/audit/6d678fbbe87e/counterexample.json`
- `checks/audit/probe_audits.py`

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-20b3349acd859fe9-v0001/audit_assets.json), manifest SHA-256 `46897dd2caa01636c02f23cd1aa8c47d33a83d1aa0a72fa63c530bc1bcc2e562`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `659439eb5d5c14675a0b054b9a7cb04b7d4ff0c6294c1abb1cfbd14d02980f8e`.

# Decisions for `6d678fbbe87e`

## D1 — Preserve the selected authority

**Choice.** Keep the canonical transformation and selected Racket program
unchanged; pin `RULE_HASH = "e0165fc03ab4"` and implement an independent Python
mirror only for generation checks.

**Rationale.** The defect was in the teaching distribution and public generator
contract, not in canonical labels.  The baseline rule smoke and authority sync
already established the selected authority, and the retained counterexample
showed a rival-discrimination failure rather than a labeling failure.

**Alternatives rejected.** Rewriting the Racket rule would add unnecessary
authority risk.  Defining the rule at the object/component level would preserve
the accidental shortcut instead of the canonical local law.

**Probe and limit.** Canonical pairs, mirror parity, rule smoke, and authority
sync pass.  This establishes parity on the checked domain, not formal program
equivalence for arbitrary malformed grids.

## D2 — Replace nine misleading axes with two exact axes

**Choice.** Advertise only `grid_h` in `4..8` and `grid_w` in `5..10`.
Both controls are exact, observable from pixels, and enforced by strict literal
integer validation.  Unknown controls are rejected.

**Prior choice reversed.** Version 2.1 exposed texture and structural knobs that
were ignored, coerced, or incompatible with the actual templates; even requested
sizes frequently did not match outputs.

**Rationale.** A smaller honest API is more useful than a broad fictional one.
Size controls preserve meaningful legal variation without claiming semantic
features the generator cannot reliably realize.

**Alternatives rejected.** Keeping dead axes as hints or silently clamping them
would continue override-contract failures and permit caller/generator mismatch.

**Failure modes and probes.** Boolean-as-integer, float, negative index, invalid
difficulty, out-of-range size, duplicate/unknown keys, and every legal size pair
are tested.  The strict override battery is green.

## D3 — Use a deterministic four-profile teaching curriculum

**Choice.** Use one isolated canonical anchor followed by three connected
multi-window templates in a four-slot cycle.

**Rationale.** Randomly hoping for a disambiguating example is insufficient for
training data.  Every four consecutive accepted pairs now contains explicit
counterevidence to the canonical-fitting object shortcuts, while retaining a
recognizable canonical-like example.

**Alternatives rejected.** All-isolated L components were the original defect.
All-connected lessons would needlessly drift from the canonical surface.
Pure random placement could still emit an entire lesson in which a shortcut
survives.

**Failure modes and probes.** A sampled lesson could begin at any schedule
residue or hold out any pair as query.  Every declared start and all four query
positions were enumerated at fixed seed 0, and a separate 300-lesson census
rotated all queries.

## D4 — Make rival discrimination executable

**Choice.** Declare the four plausible rivals
`isolated_l_components_only`, `component_bbox_completion`,
`one_completion_per_color`, and `repeat_until_stable`; provide semantic/branch
witnesses and a lesson hook that rejects surviving rivals.

**Rationale.** Correct labels alone do not guarantee useful demonstrations.
These rivals all arise naturally from the canonical examples and represent the
specific data-value failure observed in the baseline.

**Alternatives rejected.** A prose warning cannot protect downstream lesson
assembly.  An unrestricted rule-search oracle would be expensive and still
require a hypothesis language.

**Failure modes and probes.** The list is finite and may miss an undeclared
shortcut.  Tests prove each rival fits the canonical labels before requiring
connected generated lessons to refute it; the large census records refutation
for every lesson/query rotation.

## D5 — Preserve canonical anchors and profile support

**Choice.** Retain 4x5 and 4x6 canonical-scale templates and remap placeholders
to three distinct ARC colors.  Broad generation also covers the legal size
range.

**Rationale.** The repair should add disambiguating structure without replacing
the task's visual identity.  Canonical-size/palette profiles also keep the
strict profile floor meaningful.

**Alternatives rejected.** Using only larger synthetic boards would make the
semantic checks easy while weakening canonical relevance.  Copying exact
canonical inputs into training would reduce diversity and risk memorization.

**Failure modes and probes.** Profile-floor checks found canonical-like samples
in every band (easy 16/20, medium 10/20, hard 13/20), and the 300-lesson census
reported 1,171 unique inputs.

## D6 — Make difficulty observable without narrowing overrides

**Choice.** Difficulty changes broad-profile default size/orientation support;
explicit legal `grid_h`/`grid_w` requests remain valid in every band.

**Prior choice reversed.** The first repair draft accepted difficulty but
ignored it, causing defect-lint's `dead-bands` failure.

**Rationale.** A declared difficulty parameter must affect the generated
surface, but it must not secretly invalidate an advertised exact override.

**Alternatives rejected.** Band-specific override ranges would make the public
axis contract context-dependent.  Cosmetic metadata-only variation would not be
observable from pixels.

**Failure modes and probes.** A focused test first demonstrated byte-identical
bands, then verified disjoint broad defaults and complete cross-band override
support after the fix.

## D7 — Accept connected components, but keep a narrow lawful grammar

**Choice.** A lawful input has dimensions within the exact API, exactly three
nonzero colors, three or four qualifying 2x2 windows, every nonzero color
participating, and no conflicting demands.  Connected components are allowed.

**Rationale.** Requiring every target to be a separate three-cell object was the
root distribution restriction.  The revised grammar describes the actual local
rule and admits the minimum connected witness needed to separate it from object
heuristics.

**Alternatives rejected.** Accepting arbitrary noisy grids would increase
semantic risk and make generation/self-check guarantees weak.  Requiring only a
single target would underteach simultaneous behavior.

**Failure modes and probes.** The grammar is intentionally not the full
mathematical domain of the Racket rule.  Tests cover malformed grids,
nonrectangular inputs, conflicting windows, no-op/off-manifold cases, and every
generated pair.

## D8 — Treat finite evidence honestly

**Choice.** Claim only: exact canonical checks, exhaustive fixed-seed schedule
coverage, and finite sampled rival-discrimination coverage.  Do not claim
universal identifiability.

**Rationale.** Four executable rivals and 300 sampled lessons are strong,
replayable training-data evidence, but any finite rival language leaves room for
another hypothesis.

**Alternatives rejected.** Calling a zero-finding census a proof would overstate
the evidence.  Conversely, leaving the defect as “unknown” after a reproducible
shortcut and exact witness would understate it.

**Open limit.** Other seeds, undeclared rivals, or downstream assembly policies
that change the three-demo/one-query contract require their own receipt.

## Parametric completion-count route review (2026-10-24)

Added a task-local native family under `workspace/parametric/` with episode-fixed
`finish_rule=complete_only|route_dominant`. The default is the exact selected
canonical Racket source. The alternate first applies the canonical local 2x2
completions, then selects the color with the greatest number of newly completed
cells and routes only that color between aligned new targets. Inputs are matched
across settings and expose a 3/2/1 completion-count curriculum; a large solid
runner-up object makes raw input frequency a wrong intermediate.

The adapter supports independent 2--6 demonstrations and 1--4 prefix-stable
queries, including a substantive 30x30 fourth query. Public views contain only
demonstrations and the current query input. Native qualification passed both
settings on seeds 0 and 17 with four queries; the protected causal witness uses
`wrong_intermediate` and changes 69 output cells. The bounded self-audit covered
nine executable rivals, 160 sampler requests, size boundaries, canonical pairs,
and public/private projection. Two canonical-setting rival checks survived only
because the alternative was equivalent on every checked pair; no checked rival
fit the visible demonstrations and changed a query.

Evidence: `workspace/parametric/evidence/manifest.json`,
`checks/6d678fbbe87e/qualification/qualification.json`, and
`checks/6d678fbbe87e/causal/witness.json` in the review return. This is finite
reviewer evidence only. Exact-source owner acceptance and training admission are
pending.
