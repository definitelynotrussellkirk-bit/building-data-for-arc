# Current account: 374fae0ec7a2

## Intended rule
Read transform codes from `(0,0)` and `(0,1)`, erase those code cells, crop the unique connected all-9 proto component, apply code 1 and then code 2, and stamp the transformed binary shape centered on every isolated colored anchor. Each stamp is recolored to its anchor; the selected authority permits clipping at the canvas and later stamps overwriting earlier cells.

The canonical Racket authority was **not changed**. The generator pins `RULE_HASH = "664609196c7e"`; final generator SHA-256 is `3542010815c2e0504e11a947ca2fc7c6ba0fbdff1fbfb90034cd0d5334ef9eab`.

## Reversed decisions
The prior v2.0.1 source (`7c7ae515…`) advertised nine axes, including palette, density, helpful textures, and destructive degenerates. Several were inert, legal endpoints were rejected, unknown keys were accepted, and `texture="no_motifs"` produced an all-zero input that passed `self_check` but crashed the Racket rule. That prior audit was used as a lead: `review-dc64e0b5160721cf:v0001`; the retained minimal record is `counterexamples/v2.0.1-advertised-domain-runtime-failure.json`.

The new choice is a six-axis positive contract only: `grid_h`, `grid_w`, `code1`, `code2`, `proto_size`, and `n_anchors`. All are exact, observable, strictly typed integer controls; every documented endpoint is constructive. Palette/density/texture controls were removed rather than simulated because the rule gives them no independent semantic role.

## Distribution and teaching decisions
- Defaults cycle through four canonical-scale profiles and lawful 8×9 / 18×18 support profiles. The generalized profiles fixed the intermediate defect-lint warning that the advertised height range was only override-reachable.
- Connected asymmetric proto representatives cover sizes 2–6. Default size-4+ profiles make transform order and both individual codes observable; size 2–3 remain legal exact overrides.
- Default lessons use 2, 3, or 4 anchors by difficulty and choose clean, fully visible, nonoverlapping stamp footprints. Exact overrides up to 8 anchors remain lawful under the authority's clipping/overwrite semantics.
- `self_check` verifies dimensions, integer ARC cells, both code cells, an otherwise empty header, exactly one all-9 proto of size 2–6, and 1–8 isolated anchors colored 2–8.
- The semantic contract declares `reverse_order`, `ignore_first`, and `ignore_second` rivals. A three-demonstration lesson is rejected when any declared rival fits all demonstrations but changes the query.

## Evidence and limits
Final battery: 12/12 green in `checks/after-final/`. Focused regressions: 49/49 in `checks/task-tests/`. The independent oracle probe sampled 100 inputs in each of None/easy/medium/hard with zero invalid or nondeterministic draws and refuted all three rivals on every draw (`checks/reference-probe-final-v31.json`). The source-bound lesson census materialized 300 three-demo/one-query lessons and 1,200 query rotations with zero declared-rival ambiguities (`checks/lesson-census.json`).

Finite rival checks are not a proof of unique induction against every possible hypothesis. Exact high-anchor/small-canvas overrides can create clipped or overlapping stamps; those are authority-lawful contract probes, not ordinary curriculum profiles. Codes 1 and 7 are both identity under the authority and cannot be distinguished as different operations from outputs alone.
## Current reviewer considerations

Source SHA-256: `3542010815c2e0504e11a947ca2fc7c6ba0fbdff1fbfb90034cd0d5334ef9eab`.

# Decisions — 374fae0ec7a2

## D1 — Reduce the public axis surface to six exact semantic controls
**Prior choice:** v2.0.1 advertised nine axes, including palette, density, helpful textures, and destructive degenerates. The original rationale is not recorded; the likely intent was broad combinatorial reach.

**New choice:** retain only `grid_h`, `grid_w`, `code1`, `code2`, `proto_size`, and `n_anchors`.

**Why:** palette/density/texture did not independently change the selected rule and several were byte-inert. Worse, `no_motifs` could emit an all-zero input that old `self_check` accepted before the authority crashed. A small truthful contract is more valuable than nominal reach.

**Alternatives rejected:** make cosmetic palette aliases visibly different; keep negative textures behind the ordinary override API; silently clamp endpoints. Cosmetic aliases would confound fixed code/proto color roles, negative fixtures are not positive training inputs, and clamping violates exact-control semantics.

**Probes:** prior audit `review-dc64e0b5160721cf:v0001`, before override gate, exhaustive endpoint tests, and final override report.

**Failure modes / limits:** removing axes reduces superficial variety. That is intentional; variation now comes from lawful layouts, anchor colors, positions, sizes, and transform sequences.

## D2 — Keep the canonical authority unchanged and pin it
**Choice:** no Racket edit; set `RULE_HASH = "664609196c7e"` after independent canonical-pair parity checks.

**Why:** the failure originated in generator/validator contract, not the transform-and-stamp rule. Editing the authority would hide bad inputs rather than repair their source.

**Alternative rejected:** make the Racket program return a blank output for missing proto/anchors. That would legitimize malformed positives and alter the task.

**Probe:** canonical oracle parity in focused tests, rule smoke, Racket lint, and authority sync.

**Limit:** codes 1 and 7 both map to identity in the selected authority. The generator honors this exactly rather than inventing a seventh transform.

## D3 — Use a deterministic six-profile schedule
**Choice:** four canonical-scale profiles plus `generalized_min_8x9` and `generalized_max_18x18`, indexed by `sample_index mod 6`.

**Why:** canonical anchors preserve the task prior and guarantee asymmetric sequence witnesses; explicit extremes make the advertised dimension support part of ordinary sampling rather than override-only metadata. The first repaired four-profile schedule triggered a support-span warning, which the min/max profiles resolved.

**Alternatives rejected:** uniform random dimensions and codes; canonical-only dimensions; difficulty-specific dimension ranges. Uniform random sampling weakens profile-floor guarantees, canonical-only sampling makes advertised endpoints dead in defaults, and difficulty-specific ranges previously caused legal global overrides to be rejected.

**Probes:** retained red span test, intermediate warning in `checks/after-full/`, final defect-lint, 400-draw independent probe.

**Failure modes / limits:** a short deterministic period does not enumerate every layout or seed. Layout and colors remain seed-dependent; finite sampling cannot certify all possible generated instances.

## D4 — Use connected asymmetric proto representatives for sizes 2–6
**Choice:** one connected representative per exact proto size; default profiles use size 4–6 asymmetries.

**Why:** the canonical task uses one connected color-9 component. Asymmetric size-4+ shapes expose direction and transform order. Size 2 and 3 remain legal for exact contract coverage, even though some transforms are equivalent on those small shapes.

**Alternatives rejected:** arbitrary connected-polyomino sampling and disconnected templates. Arbitrary sampling needs a much larger ambiguity analysis; disconnected templates contradict component extraction.

**Probes:** canonical parity, all endpoint combinations, rival disagreements in the independent probe.

**Failure modes / limits:** the five representatives do not cover all polyomino topologies. The repair prioritizes reliable semantic teaching over unverified shape breadth.

## D5 — Clean defaults, lawful extreme overrides
**Choice:** for at most four anchors, search for fully visible, pairwise-disjoint transformed footprints. For larger exact overrides, fall back to lawful isolated anchors even when stamps clip or overlap.

**Why:** normal lessons should present readable evidence; the authority explicitly clips at bounds and resolves overlap by iteration order, so the full exact domain can remain constructive without misrepresenting the rule.

**Alternative rejected:** declare high-anchor/small-canvas combinations incompatible. A constructive fallback existed, and the selected authority defines their outputs.

**Probes:** all 256 endpoint combinations across None/easy/medium/hard in focused tests; Racket execution in the battery.

**Failure modes / limits:** extreme override outputs may be visually harder and are not used as default curriculum profiles. Overlap may obscure individual stamps while remaining correctly labeled.

## D6 — Make validation semantic rather than acceptance-only
**Choice:** parse the actual task grammar in `_analyze`, use it for `self_check`, strict profile validation, override observation, and the Python rule/rivals.

**Why:** the baseline rejected 0/60 destructive mutations and accepted blank/minimal impostors. Shared parsing prevents the validator, observer, and semantic probes from drifting on basic structure.

**Alternative rejected:** merely reject named degenerates. That would patch symptoms while preserving a toothless validator.

**Probes:** mutation tests; before/final self-check and defect-lint stages.

**Failure modes / limits:** validation establishes executable task-domain structure, not pedagogical sufficiency; the lesson contract handles the latter.

## D7 — Declare and test sequence shortcuts
**Choice:** executable rivals are reverse transform order, ignore the first code, and ignore the second code. Each lesson uses three demonstrations; `lesson_identifiable` flags a rival that fits every demo but changes the query.

**Why:** this task's central reasoning demand is sequential state. Correct individual labels are insufficient if examples permit a simpler one-code or commutative shortcut.

**Alternatives rejected:** a prose-only witness list and canonical-pair-only checks. Neither tests actual generated lessons or query rotations.

**Probes:** 400-draw independent oracle audit and 300-lesson/1,200-rotation Racket-labeled census.

**Failure modes / limits:** only named rivals were tested. No finite rival set proves unique induction; future audits should add new plausible hypotheses rather than treating this pass as completeness.

## D8 — Preserve failed evidence and audit targets unchanged
The 35-failure initial TDD run, five-failure dimension-span run, interrupted/running aggregate, and one-warning intermediate battery remain under `checks/`. Audit targets `9d488d6a3875` and `36018a11f283` were inspected and reported only; their source files were not edited.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-dc64e0b5160721cf:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7c7ae51506f22143a5e52521b90beb4929098f24e0952f01bd44d981abb88344`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Current source 3542010815c2e0504e11a947ca2fc7c6ba0fbdff1fbfb90034cd0d5334ef9eab removes destructive texture/no_motifs controls, enforces codes/proto/anchors and constructive endpoints; current notes retain the old minimal runtime-failure witness. New reviewer source-bound audit specifically checked former endpoint/validator/reference contract and reports49 tests plus12/12 battery clean. Resolves named old-source domain/authority finding only; reported, not independently rerun.

### Assessment or prior finding

## 374fae0ec7a2

**A2 — reproduced generator/validator/reference contract defect.**
`generate(0, 0, texture="no_motifs")` returns a **10-by-12 all-zero grid**.
The texture is publicly advertised, and `self_check` returns `[]`. The supported
public Racket application exits **1**, with no output and the recorded error:
`RacketBridgeError: Racket error: map: contract violation; expected: list?; given: #f`.
This is an explicit-override path, not a claim that default production draws
routinely fail. It violates the source's stated need for transform codes and a
color-9 template component; the validator permits zero codes and does not enforce
the required template. The exact input, source identities, error and null output
are retained. A rival output is not applicable to a runtime failure and is null.

A separate exact contract probe rejects advertised boundaries: code1=7, code2=7,
proto_size=2/6, grid_h=8 and n_anchors=8 all raise ValueError at seed 0/index 0
under the default band. These are advertised legal values, not malformed calls.
The canonical first training input contains **six color-9 prototype cells**,
whereas the ordinary sampler's motif request is limited to 3–5; the task's own
canonical structure is therefore not fully represented by that size control.
No claim is made that every possible placement defect has been found.

Generator SHA-256:
`7c7ae51506f22143a5e52521b90beb4929098f24e0952f01bd44d981abb88344`.
Executed/catalog rule hash `664609196c7e`; full rule-text hash and command cwd
are in `checks/audit/374fae0ec7a2/racket.json`.

Suggested action: keep invalid degenerates out of the production override API
(or have validation reject them), validate required codes/template/anchors, and
make each advertised boundary legal or explicitly change its contract. Findings
only: this audit source and authority were left unchanged.

### Reproduction

Run the preserved `checks/audit_probe.py` through `run_with_racket.py` to rebuild
the exact inputs (restore the census JSON first if compressed). Public `apply`
commands and actual exit codes are in RESULTS.json. `checks/verify_authorities.py`
checks both public application results; a nonzero apply for A2 is expected evidence
of the reproduced defect, not a failure of the repaired main generator.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-dc64e0b5160721cf-v0001/audit_assets.json), manifest SHA-256 `6a07ee9b2dc314682243fd3ee8c57f48363e6333f3ead0306a305f96d01fe3e0`.
<!-- arcpuzzles-current-audit-assessment:end -->
