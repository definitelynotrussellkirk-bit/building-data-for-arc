# Review notes — 779c7c31edc3

Assignment `review-9590ce90455a4905`; baseline version 2.0.1, replacement 3.0.0.
No other generator, shared helper, frozen root test, or Racket rule is patched.

## Reproduced problems and repair

R1: Controls were misleading. Easy examples forcibly used one rectangle, advertised
ranges exceeded the per-band choices, texture shortcuts bypassed controls, and
several palette/count aliases did nothing. Constructive slots now realize exactly
four deliberately small, observable axes. The maximum advertised count is four,
not the old unsupported six. An explicit impossible color/count combination is
rejected. Boolean/non-integer controls and unknown keys are rejected too.

R2: Unique colors made the wrong “one bounding box per color” rule indistinguishable
on all five canonical examples and baseline generated scenes. Easy single-component
lessons also admitted “hollow only the largest.” A three-profile curriculum adds
separate same-color components, multiple rectangles, and multi-cell interiors.
The final generator declares these exact executable rivals and witnesses.

R3: Canonical examples include height-five rectangles and different-color touching
components. The old summary incorrectly excluded the latter and its sampler never
produced the former. The new domain validator accepts those canonical structures
while rejecting malformed grids, non-ARC colors, non-solid components and tiny
rectangles. An explicit anchor supplies the canonical-scale floor without fixed
canonical replay. Zero background and solid rectangles remain intentional bounds.

R4: The first repair made all difficulty bands identical. The full defect linter
caught this. A regression was added before changing the weights. The intermediate
source and failing report remain in `checks/intermediate_generator.py` and
`checks/after/`; final evidence is separately under `checks/after-final/`.

## Measured verification

The initial regression suite had 16 failures / 13 passes on the baseline. The
first repair passed those 29 tests. The added band regression then failed before
its fix. The final generator suite has 35 passing tests. The new automatic replay
gate has seven tests (all seven were red before implementation), making 42 passing
task-local tests in total. The repository default suite has 178 passing tests;
its discovery configuration does not include the task-local directory.

The final 12-stage battery is green. `workspace/qualify.py` executed the actual
runner on 100 pinned lessons per band and 120 cyclic-start windows per band,
660 assembled lessons total. There were no declared rival survivors and no
independent-oracle/Racket mismatches in 2,640 pair occurrences. The cyclic windows
overlap; these are NOT 2,640 unique inputs. The report records unique counts per
population and band, generation attempts, source hashes and sampler policy.

The additional generic canonical-lookup/identity gate passed 100 actual-runner
lessons per band on this task, with no canonical replay demonstrations. It found
harmful lessons in the findings-only audit target `b7e4aaffabac` even after the
runner's duplicate filtering. The shadow audit target `99d5bc858270` rejects all
three of its canonical inputs. Neither audit target is patched here.

## Limits and next maintainer action

This is a finite-rival generator qualification, not an empirical Qwen training
result. Palette permutations, irregular objects, other backgrounds, degenerate
rectangles, arbitrary schedule samplers and all possible user overrides are not
proven identifiable. Explicit overrides can intentionally remove witnesses. The
canonical-size anchor has a visible schedule; testing all three starts limits a
local sampling loophole but is not a generalization guarantee.

Apply the returned source patch, rerun the task-local tests and final battery,
then inspect `qualification-final.json` and the source-bound solve record. The
reviewer's fresh solve honestly declares earlier rule exposure; masked-query
correctness is reserved for maintainer scoring. See the packet-root reports for
audit findings, retained failed iterations and the one proposed training-data gate.
## Current reviewer considerations

Source SHA-256: `edf24cd3f96c55d55eff868bba6b39fdcf5331a7af423681f658bcd858293041`.

# Decisions and rejected alternatives

Source identities and measurements are bound in `REVIEW.md`, `RESULTS.json`, and
the linked JSON reports. R1–R4 and A1–A2 use the same finding IDs throughout.

## R1 — make controls truthful before increasing breadth

The old source evidently used smaller grids and one rectangle as an easy-band
simplification, but the original author's broader intent is unknown. Its exact
axes, texture shortcuts and palette aliases did not form a truthful interface:
some overrides were ignored and capped random placement could underfill a scene.

Chosen design: four exact pixel-observable controls, constructive slots, and
explicit type/range/incompatibility errors. Grid dimensions are 9–18; rectangle
and foreground-color counts are 1–4, with colors <= components. Count four is a
conservative feasible maximum even on the smallest canvas with one-cell gaps.
The old count-six promise is removed rather than pretended to be supported.
Formerly ignored texture/palette/density/position aliases are intentionally rejected.
This changes the interface and is announced by version 3.0.0; callers supplying
those aliases must migrate. No quiet coercion is used to keep a legacy command green.

Rejected: keep the rejection loop and increase its attempt cap. That still cannot
promise exact realization, obscures feasibility and wastes sampling effort.
Rejected: fabricate effects for redundant palette aliases or retain degenerate
2×2/no-rectangle textures. They either duplicate a precise count axis or remove
the teaching operation. None of these limitations is hidden behind difficulty.

## R2 — connectivity must be taught, not assumed from colors

All five canonical pairs and baseline scenes give each rectangle a unique color.
Thus a per-color bounding-box program fits them without learning components. A
separate same-color component is a lawful discriminator under the unchanged
monochrome-connectivity rule. Its output was checked with actual Racket, not merely
with an agreeing Python implementation. All easy baseline lessons also allow a
largest-only interpretation, and some medium lessons expose that interpretation's
query failure.

Chosen design: cyclic `anchor`, `repeated_color`, `broad` profiles and three explicit
wrong rivals. The anchor supplies multiple rectangles and a nontrivial interior;
repeated-color scenes refute grouping by color; broad draws add count/size variety.
Same-color components receive a gap. Different-color touching is allowed, because
monochrome connectivity keeps them distinct. Rivals live in production metadata
only for verification; the correct Python oracle remains in the test workspace.

Rejected: a fully independent random profile draw. It can produce an entire
three-demo lesson without a distinguishing witness even when aggregate frequency
looks healthy. Rejected: guarantee a single special sample index but test only start
zero. The final probe checks every cyclic start as well as 100 hash-pinned lessons
per band. Explicit overrides can intentionally eliminate repeated colors or all
but one component; the un-overridden lesson guarantee is not extended to those
configurations. Other samplers, filtered/reordered schedules and arbitrary rivals
still need separate testing. The trace reports no rejections for the measured
final default lessons, rather than assuming filtering cannot matter.

## R3 — canonical support without literal replay

A 12×12 three-color anchor gives the required canonical-scale support and includes
a 5×3 rectangle. It randomizes positions, palette and other dimensions instead of
copying a public input. This covers the height-five structure absent from the old
generator. Audit A2 is concrete evidence for preferring structural anchors over
repeated literal canonical grids.

Zero background, filled rectangles, minimum dimensions 3×3 and a one-cell border
remain intentional. They isolate the operation rather than expanding into arbitrary
holes, textures, alternate backgrounds or ambiguous same-color joins. Default
sampler rectangles can be as large as 7 in a dimension. The validator permits a
broader lawful solid-rectangle domain up to 30×30 for canonical and diagnostic
inputs; it is not an exact sampler-membership test. Likewise `strict_canonical_like`
is a structural validity check, not proof of identical canonical statistics. The
separate profile-floor check is retained to make that distinction observable.

Rejected: ban all touching or enforce one color per object for simplicity. The
former incorrectly excludes a canonical structure; the latter causes R2. Rejected:
add arbitrary malformed shapes solely to diversify statistics; correct labels and
interpretability take priority over cosmetic variety.

## R4 — preserve teaching witnesses while differentiating difficulty

The first implementation used the same profile distribution for all difficulty
bands. The defect linter caught this and a failing regression confirmed it. The
fix changes weighted size/count defaults outside the anchor. Easy favors smaller
canvases and fewer broad-profile rectangles; hard favors larger ones and more.
All bands still teach the component rule. Explicit overrides have the same meaning
and legal range in every band. Difficulty is not independently calibrated against
a model, and larger grids are not asserted to be strictly harder for every solver.

The intermediate failed source/report are retained rather than replaced by the
final successful evidence. Default dimensions have overlapping support, including
canonical-scale mass, so difficulty is a weighting rather than a disjoint domain.

## Measurement and audit choices

Racket is the sole output authority. Independent local-neighbor parity is a second
check only on this solid-rectangle domain. `qualify.py` uses the actual runner and
source declarations, distinguishes pair occurrences from unique inputs, records
all schedule starts and exact hashes, and retains wrong-rival counterexamples.
No universal induction result or training-admission decision follows.

A1's counterexample is canonical and accepted by Racket but rejected by the audit
generator's documented validator; it is not mislabeled as an in-generator-domain
sample. A2 initially appeared in raw consecutive draws, some with duplicate demos.
The new replay gate then used actual duplicate filtering and still found 3/100
harmful lessons per band, versus 5/100 in the raw probe. The latter must not be
substituted for the former. A canonical-only lesson can still be intelligible to
a human; the failure is a plausible memorizer shortcut in synthetic training,
not a proof that no legitimate solver can infer the correct operation.

No audit target is patched because the assignment requests findings only. Their
source hashes and full small counterexamples allow a separate owner to reproduce
and decide whether to repair or document a domain restriction.

## Scope, verification, and stopping

The source patch stays task-local. The repository root test fixture and all
shared runtime code remain untouched. The added tools are task-local prototypes
for later shared integration, not an unauthorized framework refactor. Code was
self-reviewed and exercised by real runtime checks; no independent reviewer agent
was available or is claimed.

After generator work, a fresh visible-example solve was prepared from final bytes.
Its single genuine attempt passed all visible demonstrations. Earlier exposure
was disclosed and query labels stayed closed. Completion means the assigned
repair, evidence, audits and solve record were produced; it does not mean empirical
Qwen improvement, global generator approval or a hidden-query score was measured.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-3592fb07fc769aa3:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `fba5f06351d8e949821abe54d553058bd39daf1a369661c09a55b44deb59e0e7`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Historical corroboration only, not a new independent/current-source finding. The ticket and immutable report explicitly replay old generator SHA256fba5f06351d8e949821abe54d553058bd39daf1a369661c09a55b44deb59e0e7; the issued/current source isedf24cd3f96c55d55eff868bba6b39fdcf5331a7af423681f658bcd858293041 and was not tested. Original audit review-3f97e96eb4741d55:v0002 remains actionable and is NOT resolved or safety-cleared. Retain replay evidence in the native supplementary assessment: checks/tickets/ticket-520a041b56577462/probe.py checks/tickets/ticket-520a041b56577462/run.log checks/tickets/ticket-520a041b56577462/result.json.

### Assessment or prior finding

## 779c7c31edc3

**Reproduced the pinned historical easy-curriculum finding; this is not a current-source finding.** The ticket is bound to retained generator SHA-256 `fba5f06351d8e949821abe54d553058bd39daf1a369661c09a55b44deb59e0e7` (version 2.0.1), while the packet's current generator is SHA-256 `edf24cd3f96c55d55eff868bba6b39fdcf5331a7af423681f658bcd858293041`. No peer source was edited.

### Bound identities

- Rule hash: `8f9e53b42241`.
- Audit return: `review-3f97e96eb4741d55:v0002`; audit-record SHA-256 `8e35ecbcfa00548bc87b1cb1ac55e5e625da5206f48601b17208e2cf28c24cad`.
- Assets manifest SHA-256 `5637a7209324179a3da6f09919ee6ca55754856adaa48e5ab2c89a4c30aaffdb`; audit-index SHA-256 `cc8efbaa76acad7ae9720f8e6ca06228c8c8b0cf9c5b64ad5a9ce79c68763368`.
- Assigned probe seed: `79dfcbb99b07b4993d3963da2ee8a99f1faa87c04110c7fd324270cded20d816`.

### Reproduction

The one permitted targeted replay generated exactly three `easy` examples from the pinned old source. All three contained one rectangle (dimensions 3×3, 3×3, and 4×5), passed the old source's `self_check`, and let a shortcut that hollows only the first row-major rectangle match the protected-Racket label. The five canonical inputs contain `[3, 2, 3, 2, 3]` rectangles; on the retained three-rectangle canonical witness, the same shortcut differs from protected Racket. Canonical data also contains a 5×3 rectangle, while the old sampler restricted rectangle heights to 3..4.

This confirms the mechanism and scope of the existing old-source audit: its easy curriculum did not expose multi-object behavior or the full canonical dimension support. The replay did not test the independently changed current source and should not be used to create a current-source defect automatically.

Evidence: `checks/tickets/ticket-520a041b56577462/probe.py`, `checks/tickets/ticket-520a041b56577462/run.log`, and `checks/tickets/ticket-520a041b56577462/result.json`. Recommended disposition: retain the historical audit as reproduced against its immutable source binding; assess or close it for the current source only with a separate current-source check.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/779c7c31edc3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
