# Generator notes: 18a3c532c9dc

## Current review — 2026-10-20

This review used the accepted `review-5bbac7640f8f6861:v0001` decision and
source SHA-256 `e17135ab8b1b38e19842487666e90ff440a7492968262f4b483ed21d2bb82a9b`
as a lead, then reran the packet's checks. The selected canonical Racket rule
and `RULE_HASH = c6cdd9647cb6` remain unchanged.

The baseline battery was 11/12 green: `defect_lint` reproduced 33 invalid
runtime-scalar calls that `generate()` accepted (boolean, float, and string
`seed` / `sample_index`, plus negative `sample_index`, across three difficulty
settings). The current generator rejects non-exact integers and negative sample
indices before constructing generation context. Focused regressions watched all
11 distinct invalid values fail before the repair and pass afterward. The final
source SHA-256 is
`9700fc52f3edcf201ba01d2339fee11732ba09efbfd8d2875cd5bd624114a827`.

Final evidence for this source:

- `checks/after/checks/18a3c532c9dc_after_battery_summary.json`: all 12 stages green.
- `checks/task-tests/result.json`: 359/359 portable task tests pass.
- `checks/lesson-census.summary.json`: 300/300 three-demo/one-query lessons and
  all 1,200 query rotations have no ambiguity against the three declared
  adjacent-priority rivals; 1,200 unique inputs, zero materialization/scoring errors.
- `solve/summary.json`: exposed post-repair revision 1 passes all three visible
  examples; hidden query labels remain withheld.

A separate **prototype**, not a production API or approval change, lives under
`workspace/parametric/`. Its episode-level `priority_mode` is chosen once and is
fixed across three demonstrations and one query. `canonical` preserves the exact
canonical program bytes (`TR > BL > BR > TL`); `reversed` uses
`TL > BR > BL > TR`. Racket-derived evidence for both modes, including a lawful
setting-difference witness and source hashes, is in
`checks/parametric/priority-gallery/`. The prototype deliberately uses strong,
shuffled precedence conflicts and compares only the declared opposite setting;
it is finite instructional evidence, not a universal identifiability claim.

The current production domain and prior design rationale below remain in force.
The older final-source hashes and evidence paths in the retained history describe
the earlier accepted return and are superseded by this section.

## Retained prior design and decision history
## Intended rule

Split an even rectangular grid into TL, TR, BL, and BR quadrants. For each
corresponding coordinate, start with TL and let nonzero BR, then BL, then TR
replace it. The effective priority is `TR > BL > BR > TL`. The canonical rule
hash is pinned as `c6cdd9647cb6`; the canonical Racket authority itself was not
changed in this review.

## Current generator design (v3.0.0)

- Lawful generated inputs are 4–20 rows by 4–20 columns, independently even,
  with background 0 and one distinct nonzero color per nonempty quadrant.
- The only public exact controls are `grid_h` and `grid_w`. Invalid values and
  every unknown override fail loudly; `observe_overrides()` recovers both values.
- A keyed 8×8 anchor occurs at high rate so every difficulty band covers the
  canonical 8×8 input / four-color-plus-background profile. Other draws retain
  rectangular size diversity and band-dependent occupancy density.
- Every input reserves four shuffled coordinates that demonstrate: TR wins when
  all four are present; BL wins without TR; BR wins without TR/BL; and TL survives
  alone. Thus each generated example refutes the three declared adjacent-priority
  rivals (`BL>TR`, `BR>BL`, and `TL>BR`).
- `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, and `lesson_identifiable()` provide an
  executable, finite teaching contract. This is evidence against those declared
  rivals, not a proof of unique induction against all conceivable rules.
- `self_check()` now validates rectangularity, ARC cell values, even supported
  dimensions, one nonzero color per quadrant, and color distinctness. The same
  structural domain is exposed through `strict_canonical_like()`.

## Reversed choices and evidence

The prior generator advertised nine controls, but most were ignored or not
observable; it also exposed intentionally degenerate textures as ordinary valid
values. Those controls were removed rather than cosmetically accepted. The prior
independent sparse layouts were replaced by explicit precedence witnesses because
correct individual labels did not ensure that a three-example lesson taught the
priority order. Task-local portable regressions cover all 9×9 exact size pairs in
all four difficulty settings, invalid controls, canonical labels, semantic rivals,
query rotations, deterministic diversity, structural corruptions, and keyed
provenance on the canonical-size branch.

The selected base `target_code` had behavior equivalent to canonical but different
text. It is now synchronized exactly to canonical; the previous executable text is
retained as `raw_code` with archival role metadata. This is an authority-mirror
repair, not a change to the canonical rule or its outputs.

## Known limits

The generated domain is intentionally narrower than every input on which the rule
could execute: each quadrant uses exactly one distinct color and every example is
semantically overdetermined for the declared precedence rivals. Density is hidden
randomness rather than a public exact axis. The finite rival set does not cover
all possible geometric, color-frequency, or memorization shortcuts; larger and
novel-rival audits remain useful.

## Final evidence

- Fresh full 12-stage after battery: `checks/final-verification-battery/` (all green after checkpointed resumes).
- Portable task tests: `checks/task-tests-final/` (342 parametrized cases).
- Fresh-packet patch replay: `checks/fresh-replay/` (patch check passed; 342/342 tests passed; generator and solve hashes match).
- Large source-bound lesson census: `checks/lesson-census-final.json`; 300/300
  production lessons and 1,200/1,200 three-demo query rotations had no ambiguity
  against the declared rivals, with 1,200 unique inputs and zero scoring errors.
- Final generator SHA-256: `e17135ab8b1b38e19842487666e90ff440a7492968262f4b483ed21d2bb82a9b`.
## Current reviewer considerations

Source SHA-256: `9700fc52f3edcf201ba01d2339fee11732ba09efbfd8d2875cd5bd624114a827`.

# Decisions for review `review-824e9357d6d7dadf`

## D1 — Treat the accepted prior return as a lead, not as current evidence

The selected source had one reviewer-reported accepted decision:
`review-5bbac7640f8f6861:v0001`, source SHA-256
`e17135ab8b1b38e19842487666e90ff440a7492968262f4b483ed21d2bb82a9b`.
I preserved its intended quadrant-overlay design, then reran the current packet's
battery and task tests rather than assuming the old receipts still established the
current contract. This found a new strict-scalar defect without reopening the
already well-supported generation design.

## D2 — Fix only the public runtime scalar boundary

**Prior choice:** `generate()` passed `seed` and `sample_index` directly into
`gen_ctx`, which accepted booleans, floats, strings, and negative indices.

**New choice:** require `type(value) is int` for both runtime scalars and require
`sample_index >= 0` before any generation context is built.

**Why:** these values define deterministic sample identity. Silent coercion or
acceptance can alias intended examples, admit malformed recipe metadata, and make
replay semantics language-dependent. The baseline defect lint reproduced 33
accepted-invalid calls. Focused tests were written and observed failing before the
six-line production repair.

**Alternatives rejected:** coercing with `int()` would preserve ambiguity (`True`,
`1.75`, and `"1"` would alias valid calls). Validating only in tests would leave
other callers exposed. Refactoring shared `gen_ctx` was outside the allowed task
patch and could change unrelated generators.

## D3 — Preserve canonical behavior and authority exactly

The canonical task, Racket program, `RULE_HASH = c6cdd9647cb6`, legal generation
schedule, axes, semantic rivals, and outputs were not changed. The final battery's
rule smoke and authority-sync stages are green, and the parametric default program
is byte-for-byte the canonical program. A larger generator redesign was rejected
because no legal-input or label defect was found.

## D4 — Add one nearby rule parameter only in a separate prototype

The family supports a meaningful episode-level parameter: `priority_mode`.

- `canonical`: `TR > BL > BR > TL` (the original/default setting).
- `reversed`: `TL > BR > BL > TR` (complete reversal of the same four-quadrant
  overlay reasoning structure).

The mode is selected once per episode, not per pair. Grid splitting, quadrant
roles, corresponding-coordinate overlay, nonzero semantics, and output shape stay
invariant. Only the precedence chain changes. A color reskin, size parameter, or
occupancy-density parameter was rejected because those do not change the executed
rule. A production API change was rejected because the packet explicitly limits
parametric work to task-local prototypes.

## D5 — Make every prototype lesson identify its setting

Each retained episode uses four lawful controlled inputs with shuffled conflicts.
Every one produces different outputs under the two priority settings; therefore
all three demonstrations refute the rival before the query requires the choice.
All labels and rival outputs are obtained by applying the exact instantiated
Racket text through the protected bridge. The default is checked against all six
canonical pairs.

An early implementation evaluated the Racket lambda itself and received a
serialized procedure descriptor. The failing prototype tests exposed this. A
minimal diagnostic confirmed that applying the lambda to the bound grid returned
the canonical output, and the adapter was corrected to execute `(<lambda> g)`.
The original RED log and the final six-test GREEN log are retained.

**Limitation:** only two settings, seeds 75/76, and one declared rival per episode
are retained. The fixtures favor instructional clarity over naturalistic sampling.

## D6 — Run a large declared-rival census despite the narrow production patch

The source already had an explicit lesson hook and three adjacent-swap rivals. I
ran 100 three-demo/one-query lessons per difficulty and rotated every one of the
1,200 materialized pairs into the query position. Both production and rotation
verdicts were clean, with zero materialization or scoring errors. This was chosen
over relying on the 12-lesson semantic smoke test. It remains finite evidence;
undeclared shortcuts are not ruled out.

## D7 — Keep audit targets findings-only

For `4d730bbef8df`, I reproduced the existing unresolved teaching defect on the
current unchanged source: at seed 11/sample indices 0–3, a natural rival that
connects only NW-SE diagonal pairs fits all three demos and differs on two query
cells. For `5e8e4691afde`, I reproduced 33 accepted invalid runtime-scalar calls.
Neither source was edited, because these lanes are adversarial audits rather than
repair assignments.

## D8 — Stop the visible solve after the first supported hypothesis

The post-repair examples directly witness the complete precedence chain. Revision
1 passed all three visible examples, so additional revisions would only manufacture
failures. Earlier rule exposure was declared `yes`; no reference or private labels
were consulted during the solve, and masked-query correctness is left unknown.

## D9 — Require a fresh full-packet replay before packaging

The return patch was applied to a complete new extraction of the issued packet rather than tested only in the edited workspace. The replay preserved the final generator hash and identified exactly six task-local source changes. The reconstructed checkout then passed all 359 selected-task tests. This guards against undeclared local state, missing patch members, and evidence that cannot survive handoff.
