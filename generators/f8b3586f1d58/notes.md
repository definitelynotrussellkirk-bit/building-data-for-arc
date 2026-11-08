# Vertical Mirror Add — current repair notes

Rule hash `26d859cbdb3e` is unchanged: read each nonzero cell from the original input and copy it to `(r, w - 1 - c)`. In the completion domain, occupied reflected endpoints cannot disagree in color. Different-color collisions swap under Racket and are explicitly outside this generator grammar; same-color pairs, blanks and center-only inputs are lawful endpoints.

The v2.1.0 source `d916bb12230a248c5ce12932371289c7e8dd1ec00e7ff5eab151533d57e9cc44` ignored palette/style controls, rejected legal dimension boundaries and did not teach repeated colors reliably. The source-bound baseline at seed `1`, indices `0..3`, has a first-color rival fitting all 3 demos but omitting query output `(11, 9) = 7`. Seeds `107` and `264` similarly expose isolated-only and first-row rivals. Public Racket receipts are in `checks/mirror-probe/`.

v3.0.0 uses a four-index curriculum: canonical profile 0 has 3 distinct isolated left seeds with a canonical shape in every difficulty; profile 1 varies side and geometry; profiles 2 and 3 are mixed, have odd widths and include a center seed. Every rich default has at least 4 off-axis seeds, adjacent same-row seeds and a repeated off-axis color. Two center-bearing profiles preserve that evidence under every 3-of-4 query rotation. Broad widths start from each band's ordinary range and round upward to odd for center-bearing profiles, within `5..26`. The whole finite-rival lesson, not a branch tag, is checked.

Five independent exact controls are `grid_h` (`4..22`), `grid_w` (`5..26`), `n_cells` (`1..20`), `n_distinct_colors` (`1..9`) and `position_bias` (`left_half` / `right_half` / `mixed`). Unpinned defaults adapt to legal explicit controls; impossible explicit tuples raise a named-axis conflict. `palette_size` and `palette_kind` remain supported equal aliases for `n_distinct_colors` and `texture`, respectively; `density='mixed'` is a validated compatibility marker. They are not advertised as extra independent degrees of freedom. `None` means absent; unknown keys, coercions and conflicting aliases fail.

Style textures `sparse` / `dense` vary count proposals and layout RNG; `varied_palette` favors more colors. Explicit counts take precedence. `texture='default'` intentionally names the ordinary no-texture behavior, so it is not listed as a distinct helpful texture. Legacy `no_cells`, `all_on_centerline` and `full_right_half` are opt-in lawful endpoints, honor compatible controls, and cannot silently override explicit incompatible requests.

The initial 57 focused tests passed; the original source failed 41 and passed 16. The first after-repair battery exposed metadata issues now corrected, plus generic mutation heuristics that classify lawful mirror inputs as destructive. A broad Racket-lawful grammar accepts blanking, color permutations, row duplication, singletons and blocks; malformed arrays/colors and conflicting mirrored endpoints are rejected. The final evidence below retains those heuristic findings and checks them with explicit rule-bound fixtures; no artificial input restriction is added to manufacture a green gate.

Limits: no universal guarantee against undeclared spatial/conditional rivals, no training-accuracy claim, no approval or solve-trajectory admission. Explicit low counts, center-only/empty endpoints and constrained side overrides may not teach the complete rule and require their own actual lesson checks.

## Final evidence and current acceptance issue

Final generator SHA-256: `5055679fe703a02550117a751c367cd0d9396c320b4ade44bcde8dd762ff98c0`.

The independent review found one real center-capacity undercount: a `4x5` grid with 9 seeds at profiles 2 and 3 is feasible. Two new tests failed first; the corrected whole suite and portable task-test stage pass **59/59**. The current side observer classifies off-axis support only; an optional center seed can coexist with `left_half` / `right_half`.

The completed final battery has **10 green stages and 2 failures**: generic selfcheck mutation sensitivity and defect-lint mutation/minimal-impostor heuristics. The independent validator-contract tool preserves those errors and verifies 155 accepted lawful cases (103 unique Racket inputs, zero reference/mirror mismatches) plus 17 explicitly rejected invalid grammar fixtures. All 61 actual generic mutations and 75 named minimal impostors are lawful for this completion grammar. This evidence does not waive the gates: **Acceptance needs attention**, and `RESULTS` remains blocked by that tooling-policy decision.

The remaining final evidence is:

- **Override matrix:** 23,850 draws, 21,240 accepted and 2,610 declared incompatible; zero findings or warnings.
- **Canonical support:** strict support of `146/600 = 24.33%`; exact canonical profiles in `6/20` easy, `5/20` medium and `4/20` hard draws.
- **Production census:** 300 lessons with 3 demos + 1 query and 1,200 rotations; 0 declared ambiguities, errors or warnings on 1,200 unique inputs.
- **Fixed-seed schedule checks:** four starts in 3 bands give 12 windows / 48 rotations and 17 unique inputs.
- **Rival checks:** a 600-seed Python diagnostic has 0 ambiguous queries for each of 6 rivals; the production Racket census checks 8 distinct rivals.
- **Solves:** both pass `3/3` visible examples; the exposed phase is honestly marked exposed, and hidden scores remain unknown.

Tooling decision: retain the broad, rule-justified domain and the 2 genuine failed gate receipts. Do not manufacture validator restrictions or change shared tools within this assigned patch. Cost: the maintainer must decide the mutation-check contract before routine acceptance. The complete source-bound evidence and prioritized proposal are in `WORK/FEEDBACK_TO_CODEX.md`.


## Current owner acceptance

Accepted the scoped generator, portable tests and task-local authoring tools using the October 3 lightweight policy. All semantic batteries, Racket comparisons, censuses, solves and replay counts in the reviewer evidence remain reviewer-reported; no routine maintainer rerun or model training admission is claimed. Exact source/rule approval records bind the accepted bytes. Both random audits remain independent findings, and shared tool requests remain proposals unless separately implemented.

The implementation improvements are accepted, with G1/G2 still open: the full battery remains 10/12 and blocked, with selfcheck exit2 and defect_lint exit1. The source-bound positive/negative grammar and Racket evidence supports the documented mirror domain, but does not waive or relabel those shared checks. The lawful-mutation versus invalid-domain tool contract is retained as a pending shared request. This source acceptance is not a claim that every gate passed.
## Current reviewer considerations

Source SHA-256: `5055679fe703a02550117a751c367cd0d9396c320b4ade44bcde8dd762ff98c0`.

# Decisions for f8b3586f1d58

## Keep the reference rule

The canonical program reads every nonzero from the original input and writes its
horizontal reflection. Both sides are meaningful. A left-only ordinary sampler
was an avoidable restriction: all 600 baseline diagnostic lessons admitted the
left-only rival. The new input domain admits either/both halves and same-color
existing pairs, but excludes different-color reflected collisions because those
swap under the actual rule and are outside symmetry completion. No Racket text,
authority record, catalog or approval was changed.

## R2: Teach occurrences, rows and adjacency

Original rationale for unique colors is unknown. The old n<=9 sampling made every
color occur once, then allowed repeats only above 9. Baseline seed 1 proves a wrong
query after three unique-color demos; seeds 107/264 prove isolated-only/first-row rivals.
Each ordinary rich input now has at least 4 off-axis seeds, a repeated off-axis pigment,
and an adjacent pair in one row. Repetition uses randomized slots, independent of
the adjacent pair. Unique mirror orbits prevent overwrite collisions; positions
and colors vary rather than fixing one witness coordinate.

## Four profiles and centerline teaching

Index 0 is canonical: a randomly chosen one of 5 canonical shapes and 3 distinct
left seeds, available in every difficulty. Index 1 varies geometry and left/right
side. Indices 2/3 are mixed and include an odd-width center seed. Each 4-consecutive
window contains 3 rich profiles and 2 center-bearing profiles; any query rotation
leaves evidence for all 8 declared rivals. A single optional center-bearing
profile was rejected because it could be held out with no center-bearing demo.
The actual Racket census verifies 300 lessons/1,200 rotations, and all 4 fixed-seed
starts are enumerated separately. Those counts are finite evidence.

## R1 and R3: Controls and compatibility

The independent exact axes are h 4.. 22,w 5.. 26,n 1.. 20,nonzero color count 1.. 9, and
left_half/right_half/mixed off-axis support. Side labels ignore a center seed.
Explicit controls override proposals across difficulty bands; unpinned defaults
adapt. Impossible explicit requests raise a structured, named-axis conflict.
The first implementation counted a center seed against off-axis capacity; the
independent review supplied a 4 × 5 / 9-seed witness. Two tests failed before the fix
and passed afterward in the 59-test suite.

palette_size and palette_kind remain validated aliases; density='mixed' remains
a compatibility marker. They are removed from the advertised independent-axis
list so duplicate names do not inflate diversity claims. Alias equivalence and
conflicts are tested directly. Sparse/dense textures change count proposals and
layout streams; varied_palette favors more colors. Exact counts take precedence.
The default texture is intentionally the ordinary call, so it is not advertised
as a distinct helpful variant. Named legacy identity endpoints are opt-in lawful
inputs; they honor compatible shape/count controls and reject conflicts.

## G1 and G2: Validation and the remaining gate conflict

The generator validator recognizes the task's broad completion grammar rather
than the exact support of one random sampler. Generic blanking, recoloring,
row duplication and small shapes are lawful for this rule, so rejecting them just
to satisfy a generic mutation quota would introduce an unjustified restriction.
The current shared gates have no supported task-domain distinction here. We keep
the 2 failed gates and supply a reusable probe covering 155 lawful cases with 103
unique Racket labels plus 17 rejected malformed/collision fixtures. The cost of
this choice is explicit: this return is blocked for routine acceptance until the
maintainer decides the shared mutation contract. The tool does not bypass a gate.

## Verification boundaries

The Python 600-lesson comparison is a fast diagnostic, while all decisive baseline
witnesses and the 300-lesson production census have executed Racket labels. Solves
are visible-only; the exposed phase is recorded as exposed. No training benefit,
private-query score, universal hypothesis uniqueness or approval is asserted.
All earlier failed runs and review findings remain in checks/.
