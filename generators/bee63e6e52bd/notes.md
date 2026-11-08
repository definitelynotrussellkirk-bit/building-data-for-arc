# Current account: bee63e6e52bd v3.1.0

## Rule and authority

One nonzero, non-yellow color forms a rectangular perimeter on background 0.
Three sides are complete. The fourth retains two corner-connected arms with
one contiguous gap between them. The selected Racket rule finds the actual
arm tips, paints the cavity/mouth **band between those tip levels**, paints
the two exterior tip anchors, and continues two outward 45-degree yellow
spouts until they leave the canvas. Longer asymmetric arms can leave interior
strips unpainted; this is not a whole-cavity fill. Existing frame cells remain.

The normalized rule pin remains `eedba8f59365`; canonical data and the selected
Racket authority are unchanged. Final generator SHA-256:
`33d8f354812b25e8e5afe7555c6296040b7d63e0b6315dea5a184c5515227b3f`.
Approval remains catalog-derived. This review does not approve training use.

## Distribution and reversed decisions

The prior v3.0.0 sampler retained the correct split mouth but allowed the
canvas to clip both diagonal continuations. In a fixed 160-draw census per
band, both spouts were absent after their anchors in 77 default, 50 easy,
66 medium, and all 160 hard inputs. A Racket-confirmed medium lesson at
seed 44007, sample indices 28–31, let the no-diagonal rival fit its three
demonstrations and fail its query. The former lesson hook missed it.

Version 3.1.0 reserves two outward cells on ordinary canvases and one lateral
cell for the short 1/1 profile, ensuring that at least one actual diagonal
continuation appears in every normal generated input. Other arm profiles
already provide lateral room. This conditional margin preserves canonical
full-span 2/2 geometry. Applying the correction to every band prevents the
same clipping defect outside hard mode. The same finite census now measures
0/640 inputs with both continuations absent; these counts are geometric/Python
measurements, separate from the retained Racket checks.

Ordinary draws still use only the canonical 6x6, 7x7, 9x9 and 10x10 profiles.
Explicit `scene_profile` overrides additionally support 21x21, 21x30, 30x21
and 30x30. Large profiles scale both the frame and the available ray lengths;
they are lawful but deliberately excluded from `strict_canonical_like`.
All 256 tested large axis combinations match Racket. The large-domain guarantee
is at least one ray of three steps beyond its anchor, not that both rays
always have three steps. Large profiles are opt-in so canonical calibration
is retained in the production sampler.

Only four exact, observable axes are exposed: scene profile, opening side,
arm profile, and frame color. Frame colors are 1,2,3,5,6,7,8,9; yellow 4 is
the fixed output role. Strict request validation rejects boolean/non-integer
seeds and indices, and negative indices, including with explicit arm overrides.
Negative integer seeds remain valid. Rule helpers copy tuple rows into mutable
lists without mutating the supplied grid.

## Teaching contract and counterexamples

The period-four arm schedule is 2/2, 1/1, 1/3, 3/1. Three demonstrations plus
one query are supported, including any single held-out query among four
consecutive pairs. Every such demonstration set contains at least two
non-2/2 examples. `fixed_two_arms` fits all four canonical labels but is
refuted by those examples. `no_diagonal_spouts` keeps the band and anchors
but omits both continuations; it is refuted by the visible-spout construction.
Both rivals are executable lesson competitors and semantic witnesses.
Only fixed-two-arms is declared a canonical-fitting shortcut.

`counterexamples/fixed-two-arms.json` preserves its original v3.0.0 source
binding and pixels. The regression replays those saved pixels rather than
pretending an old version's seed recreates the same grid under v3.1.0.
`counterexamples/no-diagonal-lesson.json` preserves the newly reproduced old
lesson, its rival outputs, and Racket/source binding. Historical receipts are
evidence about their stated versions, not measurements of the new sampler.

## Tools, evidence and proposed extension

The task-local suite contains 104 passing pytest cases, including 19 prototype
cases with real Racket execution checks; no cases are skipped. The review's `checks/` contains
baseline and final gate receipts, retained red tests, a 100-per-band lesson
census, fixed-seed period enumeration, and exact audit witnesses.
`workspace/spout_coverage.py` is the reusable source-bound geometry and Racket
coverage runner; `workspace/reference_probe.py` remains an independent pixel
oracle. See the current return's REVIEW.md and RESULTS.json for final counts,
commands and fresh-patch replay results rather than treating this paragraph
as a substitute for those receipts.

`workspace/parametric/` is a separate **proposed prototype**. One hidden
episode-level `spout_reach` is chosen from full, 0, or 2. Full preserves the
canonical program exactly; finite settings retain anchors and cap only the
diagonals. The current adapter supports 2–6 demonstrations and 1–4 queries,
with four retained queries on separate count-stable streams and a 30×30 stress
case. Public names now hash the exact visible file bytes. A source-bound replay
verifier checks every private label and rejects answer/inventory tampering.
Canonical-repair acceptance does not approve these variants.

## Limits and open findings

This remains a one-frame, one-gap task with four arm profiles. Multiple frames,
obstacles, interacting pours and arbitrary arm lengths are outside the sampler.
Finite declared-rival checks do not establish uniqueness among all hypotheses,
all-seed schedule coverage, model learning gains, or measured difficulty.
The post-repair solve matches 3/3 visible demonstrations; masked query accuracy
is unknown. It records prior reviewer exposure honestly. No unresolved defect
in this selected repair was found by independent source review; actionable
findings in the two separately drawn audit targets remain for their owners.

## Current owner source and evidence limits

The canonical Racket rule is unchanged. Current production-generator claims remain those above. The separate full/0/2 prototype now has a native adapter/contract, exact public-byte IDs, 2–6 demonstration support, stable one-to-four-query prefixes, exact 12..30 teaching canvases, four-query Racket evidence, and a source/runtime-bound verifier. Historical owner exports remain preserved as historical evidence; `workspace/parametric/evidence/current` and its top-level source inventory are the current prototype artifact. Finite rival checks cover only the three declared reaches. No variant or training approval.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/bee63e6e52bd/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D15 / Parametric contract upgrade — Four-query native promotion readiness

**Choice.** Keep the existing `spout_reach` semantics and exact programs, but replace the obsolete three-demo/one-query authoring shell with a count-independent 2–6 demo, 1–4 query contract. Add a thin native adapter, typed promotion contract, exact-size 12..30 sampler, sequential first-turn projection, exact-visible-byte IDs, and a replay verifier.

**Why.** The rule parameter was already meaningful and Racket-backed. The missing work was operational: query inputs shifted when demo count changed, ordinary evidence stored one query, public names were derived from a compact projection that was not the exact bytes written, and no current verifier rebound private answers to source/runtime. Those gaps prevented clean owner qualification even though the programs themselves were useful.

**Evidence and adversarial surfaces.** The focused current-contract suite first failed on those exact gaps, then passed 43/43; the complete target suite passes 128/128. Boundary checks cover 2 and 6 demonstrations, one and four query prefixes, all four orientations, 12×12/12×30/30×12/30×30 canvases, and substantial full-rule output. The two retained adversarial surfaces are (1) a changed private query answer and (2) an undeclared extra export file; the verifier rejects both. Current Racket evidence and native qualification receipts are linked from the packet result record.

**Limits.** The teaching grammar is intentionally larger than the ordinary canonical sampler and starts at 12×12 because four post-anchor steps on both rays are not geometrically possible on the smallest canonical profiles. Adapter generation currently executes the protected Racket rule to produce labels before native qualification replays them; this is slower than a trusted Python mirror but avoids introducing a second label authority.

## Assignment review-f5920003fe481085 portable native-adapter repair

The staged task harness exposed that the prototype's native adapter called
`generate_episode()`, starting a second protected Racket bridge while the test
module already held one. Candidate construction therefore stalled in the
portable staged runtime even though the direct packet run passed.

The adapter now calls a subprocess-free `sample_episode()`. Its outputs come
from a task-local `predict()` mirror covering the exact `full`, `0`, and `2`
reach settings. Hand-positioned tests cover all four opening orientations, and
protected Racket replay remains the authority in retained evidence and native
qualification. The adapter is still unapproved and `training_admitted=false`.
