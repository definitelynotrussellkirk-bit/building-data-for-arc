# Current generator account: 9ce2dcf587b8

## Current native extension — `review-2f9d5f677fb14011`

`workspace/parametric/adapter.py` now exposes `ray_rule=both|main_only|one_bounce`.
The two retained direction rules are reused; `both` stays byte-identical to the
selected canonical source. `one_bounce` derives the main-ray boundary endpoints
from the input and uses them as the origins of one anti-diagonal continuation.
It freezes original sources and endpoints, with no recursive bouncing.
This is an input-derived geometric intermediate, not iterative-state evidence.

The separate native grammar extends dimensions to 7–30 and counts to 1–10
same-color interior, separated, non-diagonal markers. Production remains 7–17
and 1–3. Native requests independently support 2–6 demos and 1–4 queries,
defaulting to 3/4, with a fixed ten-input bank before slicing. The first-two-demo
teaching check and six-demo native qualification serve different purposes.

An adversarial review found that the original two/four-marker cores taught an
extrema-only shortcut: all their sources were outermost in each occupied row
and column, while large queries had interior sources. Protected Racket confirmed
the wrong rule fit both demos but disagreed on queries for all three settings
and both tested seeds. The second core is now a five-marker cross with unequal
arm lengths, retaining two demos and refuting row-only, column-only and combined
extrema selection. Before/after evidence is in
`checks/9ce2dcf587b8/native-teaching-before/` and `native-teaching-final/`.

Current focused evidence: 53 native/retained-prototype tests and five audit tests;
the protected audit checked 36 exact programs with 192 distinct evaluations,
refuted all 82 declared rival/episode comparisons using demonstrations, and
checked labels for every bank position at seeds 0/17. This is finite evidence,
not universal uniqueness. The template bank varies translations, colors and
axis-preserving symmetries; unrestricted layout sampling is not claimed.
Native inventory, qualification/execution, causal witness/replay, and current
single-query previews are the handoff under `checks/9ce2dcf587b8/`; exact-source
owner qualification and acceptance remain separate. No training admission.

## Intended rule and authority

A zero-background grid contains one to three markers of one nonzero color. Each original marker remains present and paints every still-zero cell on all four diagonals out to the grid boundary. Generated markers are interior, separated, and never share a diagonal, so this generator deliberately teaches the nonblocking part of the canonical rule.

- Generator version: `4.1.0`.
- Final generator SHA-256: `02e3520b866eac21bfc6eeec539bf9647d75abfc320c2dad4c8729f4ad6e3f2d`.
- Canonical pin: `RULE_HASH = "e635bf3ddbe0"`.
- Canonical/selected Racket text SHA-256: `250e7aac18a97551bde1c0c5099cbeefcde841efeebab13569f81c7f07369a24`.
- The canonical Racket program and selected authority were not changed by this repair; archival `raw_code` remains separate.

## Current input contract

The exact axes are `grid_h` (7..17), `grid_w` (7..17), `fgc` (1..9), and `n_dots` (1..3). Unknown axes, invalid values, invalid difficulty strings, non-integer/bool seeds, non-integer/bool sample indices, and negative sample indices fail loudly. Even sample indices provide exact 7×7, 15×15, and 17×17 canonical anchors; odd indices provide difficulty-skewed rectangular variation. Backtracking places the exact requested marker count without retry caps or silent shortening.

## Reversed teaching decision: color/count coupling

**Prior choice.** Source `38d9f9faace1dda2375f755099b8108ae286551d969ca4cce438667df34bb0a8` used `n_dots = 1 + sample_index % 3` and a color cycle that made colors 1/4/7 always mean one marker, 2/5/8 two, and 3/6/9 three. A color-quota rival therefore matched 360/360 default draws across sample indices 0..89 in each of four bands, even though all 27 color/count combinations were legal exact overrides. It also fit all four labeled canonical examples.

**New choice.** A 45-slot joint schedule covers all 27 color/count pairs and oversamples the combinations needed to refute that rival. Every cyclic five-pair window—the four demonstrations plus any one query position—contains at least two color-quota counterexamples. The exact before/after account is retained in `counterexamples/color-count-coupling-before.json`; `checks/schedule-repair.json` records the final schedule and window counts.

**Rejected alternatives.** Independent short color/count cycles still leave unsafe five-pair windows; simply deleting the rival declaration would hide the defect; random sampling would not guarantee arbitrary query rotations. Searches with the fixed 1/2/3 local count cycle found no qualifying schedule at periods 36, 39, or 42; period 45 was the first retained construction.

## Truthful semantic contract

`CANONICAL_SHORTCUTS` now contains exactly the two rivals that truly fit every labeled canonical pair: `first_marker_only` and `color_quota_first_markers`. Four noncanonical heuristics remain ordinary `LESSON_COMPETITORS`: orthogonal rays, one diagonal axis, fixed color 1, and source erasure. The independent task-local probe checks the declarations themselves rather than copying a rival-name list.

Final evidence, all bound to the final generator SHA above:

- 71/71 portable task tests passed (`checks/task-tests-final/result.json`).
- The complete 12-stage after battery is green (`checks/after/checks/9ce2dcf587b8_after_battery_summary.json`).
- Fixed-seed declared-period census: 135/135 four-demo lessons materialized across easy/medium/hard; 0 production ambiguities and 0/675 ambiguous query rotations (`checks/schedule-period-s0.summary.json`).
- Wider production-sampler census: 300/300 lessons, 1,396 unique inputs, 0 production ambiguities and 0/1,500 ambiguous rotations (`checks/lesson-census.summary.json`).
- Independent exhaustive task probe: 225 rotated lessons, no ambiguities or self-check failures, and all six declared competitors refuted (`checks/schedule-probe.json`).

These are finite checks against declared rivals, not a proof of unique induction against every possible program.

## Parametric extension (proposed, not canonical)

`workspace/parametric/` contains a runnable two-setting prototype for one episode-level parameter, `diagonal_axes ∈ {both, main_only}`. The `both` setting reuses the canonical Racket text exactly; `main_only` changes only the direction list to the NW–SE axis. Each retained episode has three demonstrations and one query, every pair distinguishes the two settings, and exact Racket execution agrees with the Python mirror. Final evidence is `checks/parametric/verification-final.json`.

This prototype is not catalog-approved or integrated into the production generator. It covers only two retained seeds/settings and intentionally uses one interior marker per pair to make the parameter identifiable without changing object roles, color behavior, source preservation, or boundary extent.

## Known limits

The production domain excludes mixed marker colors, edge markers, more than three markers, grids outside 7..17, and markers that lie on one another's diagonal. Those exclusions avoid unresolved collision/blocking semantics rather than claiming to cover them. The post-repair visible-only solve passed 4/4 demonstrations but was correctly recorded as exposed because the reviewer had already inspected the rule during repair.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-134d82626bc7bd77:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `38d9f9faace1dda2375f755099b8108ae286551d969ca4cce438667df34bb0a8`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit resolution on02e3520b:45-slot schedule crosses all27 color/count pairs, minimum2 color-quota refutations percyclic5-pair window; truthful2 canonical shortcuts replace four invalid declarations while retaining useful ordinary rivals. Reviewer71 portable tests,12/12 final battery,135 fixed-seed lessons/675 rotations and300 broader lessons/1500 rotations with0 ambiguity. Old audited38d9f9fa source preserved; seed0 and finite-rival scope only, no owner task rerun.

### Assessment or prior finding

## 9ce2dcf587b8

Default schedule confounding reconfirmed; false canonical-shortcut declarations.

Audited selected generator SHA-256: `38d9f9faace1dda2375f755099b8108ae286551d969ca4cce438667df34bb0a8`.
Canonical `program_solution` SHA-256: `250e7aac18a97551bde1c0c5099cbeefcde841efeebab13569f81c7f07369a24`; declared normalized rule hash: `e635bf3ddbe0`.
The target generator, notes, and canonical rule were left unchanged.

### A9.1 — Reconfirmed teaching support gap: marker color determines marker count

The current audit index already retains this finding from `review-0be3585dc452b055:v0001` against the same source. This audit independently reproduces it and does not claim it as a new discovery.

The default sampler sets `n_dots = 1 + sample_index % 3` and `fgc = 1 + sample_index % 9`. Consequently colors 1/4/7 occur only with one marker, 2/5/8 only with two, and 3/6/9 only with three. The deterministic rival **preserve every input marker, but emit diagonal rays from only the first `1 + (fgc - 1) % 3` row-major markers** processes every marker on every unoverridden default draw. This follows directly from the two schedule expressions and is independent of seed or band.

Fresh direct sampling used indices 0..26, seeds `810000 + sample_index`, and difficulties `None`, `easy`, `medium`, and `hard`. The rival matched an independent Python mirror on **108/108** inputs; all inputs passed `self_check`. It also matched all **4/4 recorded canonical labels**, whose inputs each contain a single marker. All **27/27** color/count cross-products on a 7x7 canvas were constructible, exact, and validator-accepted through advertised overrides.

The retained witness is a genuine generator result: `seed=4242`, `sample_index=0`, `difficulty="easy"`, overrides `grid_h=7`, `grid_w=7`, `fgc=1`, `n_dots=3`. The returned markers are `(1,2)`, `(4,1)`, and `(5,4)` in zero-based coordinates. It passes `self_check` and realizes every requested axis. It lies in the documented and override-emitted domain, but cannot occur in the unoverridden schedule. It is not a validator-invalid mutation. Fresh supported Racket apply finished with exit 0, confirmed executed/catalog rule hash `e635bf3ddbe0`, and produced a valid output. That authoritative output exactly matches the independent mirror and differs from the rival at **10 cells**. `probe.json` retains the differing positions and exact apply-artifact hash. The apply receipt's callable-text hash is separate from the raw canonical `program_solution` hash stated above.

Repair recommendation, not applied: decouple the default color/count cycles while retaining consecutive-window teaching coverage; add this canonical-fitting rival and a verified color/count counterexample witness. A 27-position schedule can cover all color/count pairs while retaining a local 1/2/3 count cycle.

### A9.2 — New declaration defect: four `CANONICAL_SHORTCUTS` do not fit canonical labels

The generator sets `CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)`. Fresh execution of each callable against every canonical labeled pair gives:

| Declared shortcut | Canonical mismatches |
|---|---:|
| `orthogonal_cross` | 4/4 |
| `one_diagonal` | 4/4 |
| `first_marker_only` | 0/4 |
| `fixed_color_one` | 4/4 |
| `erase_sources` | 4/4 |

All four canonical inputs pass `self_check`, and the independent Python mirror matches all four recorded labels. This is a false semantic declaration, not a generated-label mismatch. The current `docs/SEMANTIC_GATE_CONTRACT.md` requires every declared canonical shortcut to fit every usable canonical label. `shared/tools/generator_semantic_gate.py` marks such mismatches `invalid_declaration` and appends hard errors. I did not run a full semantic gate or battery for this audit; the exact callable comparisons and current contract implementation establish the violation without that staging work.

Repair recommendation, not applied: retain the four useful noncanonical rivals in `SEMANTIC_RIVALS` / `LESSON_COMPETITORS`, and restrict `CANONICAL_SHORTCUTS` to rivals actually fitting all canonical labels. The color-quota rival in finding A is another legitimate canonical-fitting declaration, but needs generated counterexample coverage.

### Reproduction and retained evidence

From `WORK/`: `PYTHONDONTWRITEBYTECODE=1 python3 checks/audit/9ce2dcf587b8/audit_probe.py`.
The probe uses the public `reviewer_support.load_selected_generator` and `canonical_pairs` helpers, reads the selected task only, and writes under its audit directory. `probe.json` retains source/rule hashes, exact populations, canonical identities, per-case observations, validator results, and witness provenance. `input.json` and `rival_output.json` retain the minimal 7x7 witness. `commands.json` records actual commands, cwd, exits, captured probe output, and the parent-executed serialized Racket command. `racket.json` contains the fresh authoritative apply result. These finite tests do not claim general semantic safety or new generator approval.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-134d82626bc7bd77-v0001/audit_assets.json), manifest SHA-256 `6c75947a4851713c76782b8645b014adca4bfaf39d4e9724c36672dad00822b4`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `02e3520b866eac21bfc6eeec539bf9647d75abfc320c2dad4c8729f4ad6e3f2d`.

# Decisions for 9ce2dcf587b8

## D1 — Preserve the canonical authority

The intended transformation is unchanged: preserve every nonzero marker and paint its color along all four diagonals through still-zero cells to the boundary. I did not alter canonical Racket text, the selected target, or `RULE_HASH = "e635bf3ddbe0"`. The canonical/selected text remains SHA-256 `250e7aac18a97551bde1c0c5099cbeefcde841efeebab13569f81c7f07369a24`.

**Rejected alternative:** modify the rule to define interactions between differently colored or diagonally aligned sources. The selected generator intentionally excludes those cases; inventing collision semantics would change the task rather than repair its curriculum.

## D2 — Treat only true canonical-fitting rivals as canonical shortcuts

The baseline declared five `CANONICAL_SHORTCUTS`, but canonical replay showed that only `first_marker_only` fit all labeled canonical pairs. A retained audit also identified `color_quota_first_markers`, which fits all four canonical labels but was undeclared.

The final contract therefore declares exactly:

- `first_marker_only`
- `color_quota_first_markers`

The four other heuristics remain `LESSON_COMPETITORS`/`SEMANTIC_RIVALS`, where generated examples may refute them without falsely claiming they explain every canonical label.

**Failure mode guarded:** a semantic gate can otherwise report “canonical shortcut refuted” for a heuristic that was never canonical-compatible, making curriculum evidence look stronger than it is.

## D3 — Replace the coupled color/count cycle with a 45-slot joint schedule

The prior schedule made marker count a deterministic function of color. Retained source-bound evidence showed a color-quota rival matching 360/360 default draws, while 27/27 color/count cross-products were legal under exact overrides. That is a training-data defect: correct individual labels still teach a shortcut.

The final schedule keeps the readable local marker-count cycle `1,2,3` but uses three 15-slot color rows. It satisfies all of the following:

1. all 27 legal `(fgc, n_dots)` pairs appear;
2. each cyclic five-pair window contains at least two examples where marker count exceeds the color-derived quota;
3. every start residue and every query position is identifiable against all declared competitors;
4. canonical profile anchors remain available in every difficulty band.

Searches with the same count-cycle constraint found no qualifying schedules at periods 36, 39, or 42. Period 45 was retained because it is the first construction found that gives deterministic arbitrary-rotation coverage without randomized rejection sampling.

**Rejected alternatives:**

- independent short cycles: cover the cross-product eventually but leave unsafe five-pair windows;
- purely random colors/counts: no guarantee for a particular exported lesson;
- delete the rival: hides rather than repairs the shortcut;
- force every example to be a counterexample: unnecessarily narrows natural support.

## D4 — Validate the public call contract before any sampling

The baseline accepted arbitrary difficulty strings, booleans/floats as `seed` or `sample_index`, and negative sample indices; one float reached the scheduler and raised an incidental `KeyError`. The final generator now validates at the source boundary:

- `seed` must have exact type `int` (not `bool`);
- `sample_index` must have exact type `int` (not `bool`) and be nonnegative;
- difficulty must be one of `None`, `easy`, `medium`, or `hard`;
- unknown axes and non-integer exact-axis values fail loudly.

**Rejected alternative:** rely on hashing/modulo internals to coerce unusual values. Silent coercion makes deterministic replay and defect diagnosis unreliable.

## D5 — Retain exact, nonblocking geometry

The repair keeps the existing four observable axes: `grid_h`, `grid_w`, `fgc`, and `n_dots`. Marker placement uses backtracking to honor the requested count exactly. Markers are interior, pairwise Chebyshev distance at least three, and never share a diagonal.

This is a deliberate scope decision, not an assertion that blockers are irrelevant to every conceivable version of the rule. It keeps labels unambiguous while still varying dimensions, color, count, and placement.

## D6 — Add a separated episode-level parametric prototype

The original-family priority asked for a small rule parameter that preserves the reasoning pattern. The selected prototype parameter is:

`diagonal_axes ∈ {both, main_only}`

- `both` is the exact canonical program.
- `main_only` changes only the direction list to `((-1 -1) (1 1))`.
- Selection is deterministic from the episode seed and is shared by every demonstration and query.
- The objects, marker role, same-color painting, source preservation, zero-cell condition, and boundary extent are unchanged.

The retained seeds 20261020 and 20261021 select opposite settings. In each episode all three demonstrations and the query disagree with the rival setting under exact Racket execution. Program hashes and public challenges are in `checks/parametric/verification-final.json` and `generators/9ce2dcf587b8/workspace/parametric/`.

**Rejected alternatives:** variable ray length changes the boundary relation; source erasure changes an object role; color remapping introduces a second reasoning mechanism; per-example parameter selection would make a single episode internally inconsistent.

**Limit:** this is a proposed prototype only. It is not wired into canonical production, catalog approval, or training admission.

## D7 — Verification and stopping rule

The final generator source is SHA-256 `02e3520b866eac21bfc6eeec539bf9647d75abfc320c2dad4c8729f4ad6e3f2d`. Work stopped after:

- 71/71 portable task tests passed;
- all 12 after-battery stages were green with the fixed-seed census attached;
- 135/135 declared-period lessons and 0/675 query rotations were ambiguous at seed 0 across three bands;
- 300/300 production-sampler lessons and 0/1,500 query rotations were ambiguous, spanning 1,396 unique inputs;
- the independent 225-lesson task probe had no ambiguity or self-check failure;
- both parametric settings passed exact Racket/Python verification;
- the post-repair visible-only solve passed 4/4 examples and was frozen with prior exposure recorded as `yes`.

Remaining domain exclusions and the finite-rival nature of the proof are documented rather than expanded into unrequested rule changes.
