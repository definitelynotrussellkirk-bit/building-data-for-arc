# Working notes: 857238219e77

## 2026-10-05 review `review-676ce432d2a571b8`

Baseline v1.3.0 produced only convertible interior length-3 runs. Labels were correct, but the ordinary distribution supplied no evidence for exact length, edge exclusion, or fresh-blank output; three canonical-fitting shortcuts therefore survived.

Version 2.0.0 replaces the sampler contract without changing the Racket authority. Every ordinary input contains 1–5 targets and exactly one interior length-2, interior length-4, and edge length-3 distractor. Public axes were reduced to five exact pixel-observable controls, `RULE_HASH` was pinned to `fc2cfb863af5`, and task-local witnesses/rivals/tests were added.

Final generator SHA-256: `313047a5064241054a183f9c4846c3e7078ee9dd70aacf538d191005faf8faa9`.

Retained evidence:
- full after battery: `checks/after/checks/857238219e77_after_battery_summary.json` (12/12 green);
- portable task tests: `checks/task-tests/result.json` (45/45 passed);
- lesson census: `checks/lesson-census.json` (300 lessons, 1,200 query rotations, zero ambiguity against declared rivals);
- deep audit: `checks/deep-audit.json` (12,000 joint controls, 4,800 rotations, 68 Racket parity grids, zero failures).

Limits: finite declared-rival checks do not prove universal induction. The regular one-short/one-long/one-edge composition is deliberate teaching structure and may itself be learnable, although it cannot change the authority's per-run classification.
## Current reviewer considerations

Source SHA-256: `313047a5064241054a183f9c4846c3e7078ee9dd70aacf538d191005faf8faa9`.

# Design decisions for 857238219e77

## D1 — Replace the axis surface instead of preserving inert compatibility names

**Original rationale:** unknown. Version 1.3.0 advertised palette kind/size, position bias, density, and texture controls, but several were aliases, constants, ignored, or included intentionally invalid negative fixtures in the ordinary domain.

**Decision:** expose only `grid_h`, `grid_w`, `target_count`, `n_distinct_colors`, and `edge_side`. Each is exact, validated before sampling, and recoverable by `observe_overrides` from the produced pixels. Unknown, retired, mistyped, Boolean-as-integer, or out-of-range controls fail loudly.

**Alternatives rejected:** retaining names as no-op compatibility shims would keep producing dishonest metadata; marking all of them diagnostic would still complicate downstream sampling without adding data variation. The strict override battery made 32,760 draws with no findings (`checks/after/checks/857238219e77_after_override_results.json`).

**Failure mode / limit:** downstream callers that relied on an undocumented old no-op now receive an error. That is intentional because silent acceptance was the defect.

## D2 — Put all three decisive negative categories in every ordinary example

**Original rationale:** the baseline sampled only target trios, apparently prioritizing clean positive examples. That left exact length, edge exclusion, and blank-output behavior unobservable.

**Decision:** every ordinary grid contains one interior length-2 run, one interior length-4 run, and one edge length-3 run, in addition to 1–5 targets. This makes each individual pair refute the three canonical-fitting shortcuts, so any three-demo lesson and every allowed query rotation remains identifiable against the declared set.

**Alternatives rejected:** probabilistic negatives would require resampling complete lessons and could still create ambiguous windows; a fixed curriculum in which different examples teach different exclusions would make query order matter. The lesson census and deep audit show zero ambiguous production windows and rotations (`checks/lesson-census.json`, `checks/deep-audit.json`).

**Failure mode / limit:** the regular “one of each” composition is learnable. It does not change the answer function, but future versions could randomize counts after preserving a per-lesson coverage contract.

## D3 — Use constrained placement rather than rejection after drawing

**Decision:** deterministic backtracking places the long run, edge run, targets, and short run. It enforces input separation, disjoint target outputs, and reserves the clipped output footprint of the edge rival before target placement.

**Probe that changed the design:** an earlier implementation allowed an edge-rival output to coincide with a true target output, so a generated example could contain the edge witness but fail to distinguish the rival. The focused contract caught that; reserving the rival footprint made the witness semantically effective for every draw.

**Alternatives rejected:** unbounded redraw loops obscure impossible combinations and weaken determinism. Painting first and validating later also makes exact overrides fragile on the 6×8 / five-target corner.

**Failure mode / limit:** backtracking cost grows with future object counts. At the current maximum of eight placements it completed every one of 12,000 exact joint draws.

## D4 — Color the contact graph, then add extra colors without merging runs

**Decision:** model horizontal contacts between placements, two-color each bipartite component, and recolor vertices with spare base-class membership to realize three or four colors. This guarantees all requested colors are visible and adjacent placements of the same color cannot merge into non-vertical objects.

**Alternatives rejected:** assigning colors independently can merge horizontally adjacent cells; forbidding all adjacency wastes scarce cells in the minimum grid. A separate color per placement would violate the 2–4 color contract.

**Failure mode / limit:** this depends on contacts joining neighboring columns, which makes the graph bipartite. The code raises rather than silently miscolors if that invariant is ever broken.

## D5 — Recur canonical dimensions while retaining the full truthful domain

**Decision:** the first three residues out of ten recur the canonical 7×9, 6×10, and 8×8 shapes when dimensions are not overridden. Other draws use the full 6–15 by 8–17 legal range with difficulty weighting; exact overrides always win.

**Alternatives rejected:** sampling only canonical sizes would constrain diversity, while purely broad random dimensions failed to guarantee the profile-floor check in small samples. Fixed canonical positions or colors were not copied.

**Failure mode / limit:** shape recurrence is intentional schedule structure. `workspace/audit_distribution.py` reports histograms so future reviewers can detect if it dominates more than intended.

## D6 — Declare concrete rivals and say exactly what the result proves

**Decision:** retain pure Python implementations for rotate-all-interior-runs, convert-edge-trios, preserve-non-targets, and identity, plus witness predicates tied to the first three. Tests first prove the three shortcuts fit every usable canonical pair, then prove generated lessons refute them.

**Alternatives rejected:** a witness-frequency count alone does not prove a witness changes a rival's answer; naming rivals without checking canonical fit can manufacture irrelevant tests. The independent reference probe and Racket batch check avoid circularly comparing the generator to itself.

**Failure mode / limit:** this is finite hypothesis testing, not a proof of unique induction. Undeclared shortcuts remain possible and are explicitly reported as unknown.

## D7 — Keep the canonical Racket program unchanged

**Decision:** no authority edit was justified. Rule smoke already passed 120/120 before repair, and the problem was the sampled input support and teaching contract rather than labels. The final authority-set SHA-256 is identical to baseline, and execution parity remains green.

**Alternative rejected:** changing the Racket rule to match the positive-only generator would erase the task's actual boundary rather than teach it.

## D8 — Add reusable tests and a deep-audit command

**Decision:** `tests/test_generator_contract.py` covers authority pinning, controls, negative support, deterministic sampling, canonical shortcut fit, lesson rotations, Racket parity, and mutation sensitivity. `workspace/reference_probe.py` supplies an independent parser/oracle; `workspace/audit_distribution.py` exhausts legal joint controls and emits a machine-readable report.

**Failure mode / limit:** the parity sample is finite (68 grids) because Racket startup is expensive. Python-only control and lesson checks are exhaustive over their declared finite schedules, and the shared 120-case rule smoke provides additional authority coverage.
