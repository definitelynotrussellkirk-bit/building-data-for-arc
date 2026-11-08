# Working notes: 3ae696dbdba9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review: no generator rewrite justified

The selected generator and Racket authority were retained unchanged after the exact battery, full 459-case override matrix, and a source-bound 100-lessons-per-band semantic census passed. The apparent override failure during review was an outer-process cutoff: the exact checker completed 41,310/41,310 draws across 459 cases and three bands with no rejection.

Durable additions are in `tests/test_generator_3ae696dbdba9.py` and `workspace/semantic_census.py`. The lesson regression requires every declared competitor to be contradicted by a visible demonstration in every sampled lesson; the census balances all five cyclic starts and records canonical shortcut counterexamples, witness counts, uniqueness, domain limits, and source hashes. This evidence is finite and rival-declaration-bound, not a claim of universal identifiability. The main known limitation remains the finite five-family morphology curriculum.
## Current reviewer considerations

Source SHA-256: `37e1557379cfe5bdf93bab8b7032aec9b4f884b6691ce3b2ec2f0840fa7b18ef`.

# Decisions: 3ae696dbdba9

## D1 — Retain the selected generator and Racket authority unchanged

**Original rationale.** The imported notes describe a five-profile, canonical-linked schedule designed to keep repeated colors, non-frame shapes, long gaps, extra components, controls, and boundary contact visible while remaining auditable. The selected rule is already pinned to normalized hash `116e45f72631`.

**Alternatives considered.** I considered replacing the finite motif set with a broader procedural grammar, declaring constrained override combinations incompatible, memoizing the shape packer, or changing profile weights. I rejected all four for this review: profiling showed no packing stall, the exact override matrix had no rejected combination, all gates were green, and no model/monitor evidence showed motif memorization.

**Probes.** Exact before/after batteries; 459-case override contract; task-local 9-test suite; 300-lesson source-bound census; canonical shortcut Racket counterexample.

**Failure modes / limitations.** Five morphology families can still be memorized. The census only covers declared rivals and finite seeds. A future expansion should be justified by downstream error evidence and must preserve exact override observability, canonical support, and every visible-demo rival rebuttal.

## D2 — Diagnose the override stage before changing placement code

The first battery attempts were cut off by the caller while the override checker was still computing. A targeted profiler ran all 1,377 case/band combinations once: every call completed, median generation time was about 2.2 ms, and there were no stalls. The exact official run then finished in 212.77 seconds with 41,310 accepted draws. Therefore the root cause was orchestration duration, not recursive packing or an impossible advertised tuple.

Rejected alternative: add memoization or incompatibility declarations merely to make an external timeout disappear. That would change behavior without addressing a generator defect.

## D3 — Strengthen lesson tests at the visible-demo boundary

The prior test checked `lesson_identifiable(demos, query)`. That hook only reports a rival when it fits every demo and then differs on the query; a rival that fits the whole lesson can evade that formulation. The added regression directly requires each declared `LESSON_COMPETITORS` function to disagree with at least one visible demo in each of 100 lessons per band. This is stronger while remaining finite and source-bound.

Failure mode: named-rival completeness is not universal identifiability. New plausible rivals must be added to the declaration and rerun through the census.

## D4 — Add a reusable semantic census rather than a one-off notebook

`workspace/semantic_census.py` imports the selected generator from an explicit prepared runtime and refuses an escaped import. It reads the generator's actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, schedule, and example count rather than copying names. It records source hashes, exact sampling formulas, unique-input counts, all cyclic starts, canonical fit, generated disagreements, first exact counterexamples, invalid inputs, and domain limits.

The tool labels with the task-local Python mirror. This is acceptable only together with authority/rule-smoke evidence; the report says so explicitly. It does not admit training data or claim general model performance.

## Input-distribution choices retained

| Choice | Retained rationale | Alternatives considered | Probe / evidence | Failure mode / limit |
|---|---|---|---|---|
| `grid_h` 10..16, `grid_w` 12..20 | Includes exact 10×15 and 10×16 canonical anchors plus larger generalizations. | Uniform large grids; canonical-only sizes. | Profile floor: exact support in every band; override matrix exact. | Size may become a profile cue; finite range. |
| `component_count` 2..5 | Separates the canonical three-object scene from two-, four-, and five-component generalization. | Fixed three; unbounded counts. | Override contract and `more_than_two_fillable_components` witness. | Counts above five are not taught. |
| `max_gap_columns` 1..3 | Refutes “first column only” while keeping objects compact. | Canonical 1/2 only; arbitrary widths. | `first_gap_column_only` differs on 1,200/1,500 census inputs. | More than three affected columns is outside selected domain. |
| `gap_profile` short/mixed/long | Distinguishes one-cell from multi-cell vertical runs. | Only canonical mixed gaps. | Short and long witness counts in every band; `short_gaps_only` refuted in all lessons. | Only the selected run templates are sampled. |
| `control_mode` none/one | Teaches that already column-convex components remain unchanged without requiring every scene to contain one. | Always one control; no controls. | 400 control witnesses per 500 inputs per band; override exactness. | Multiple simultaneous controls are not sampled. |
| `color_mode` distinct/reused | Repeated colors are the decisive rebuttal to whole-color closure. | Canonical distinct-only palette. | Global-color rival fits 3/3 canonical pairs but disagrees on 600/1,500 generated inputs. | Reuse patterns are finite and usually pairwise. |
| `edge_profile` interior/touching | Separates the rule from a hidden margin requirement. | Interior-only canonical style. | Exact override observations and boundary profile. | More varied clipping/topology is not procedurally exhaustive. |
| Five-profile cyclic schedule | Four-demo windows omit at most one profile while repeated-color evidence appears in two profiles. Two anchors retain canonical transfer. | IID profile sampling; longer cycle. | All five cyclic starts × 100 lessons/band; zero surviving declared rivals. | Deterministic residues can be learned as curriculum position. |
| Finite auditable motifs | Makes witness/rival claims inspectable and exact. | Unbounded random connected shapes. | 1,185 unique inputs of 1,500; 88–89% pair diversity in official probe. | Motif memorization remains the main known limitation. |

## D5 — Preserve separate solve and audit evidence

The initial blind solve was completed before opening the target. The final exposed solve is prepared from the final generator bytes and declares prior exposure honestly. Audit findings were saved under `checks/audit/` with exact Racket outputs and source hashes; audit targets were not modified.
