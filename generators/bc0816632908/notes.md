# Working notes: bc0816632908

## 2026-09-28 generator review

- The imported `2.0.1` generator reduced every foreground component to a singleton black cell. That made the component rule observationally equivalent to pixel selection and did not resemble the canonical multi-cell zigzag objects.
- The strongest canonical rival is a fixed 3x12 row/column pixel stencil. It reproduces all four canonical outputs exactly.
- Version `3.0.0` replaces the singleton distribution with a deterministic three-profile curriculum: `canonical_zigzag`, `shape_mix`, and `row_order_trap`.
- The authoritative Racket rule was retained. `RULE_HASH` is pinned to `6868d528f0b2`; the selected base `target_code` was synchronized to the canonical source while archival `raw_code` remains preserved.
- Negative textures and decorative colors were removed. Under the selected Racket rule, every non-2 component is a semantic foreground object, so a “decoy” color is not actually harmless.
- `self_check` is fail-closed and validates palette, component count, compactness, unique leftmost columns, whole-object observability, and minimum change rate.
- Semantic contracts now name six rivals, four witnesses, the canonical shortcut, and a three-example lesson-identifiability check.
- Focused regression suite: 21 tests. Key red/green logs are retained under `checks/tdd_*`.
- Final semantic preflight: strict canonical rate `208/600`, canonical inputs `4/4`, witnesses `4/4`, rival claims `4/4`, and lessons `12/12` across all three difficulty bands.
- Exact shortcut evidence is documented in the root `QUESTION_ANSWER.md` and `checks/shortcut_racket_probe.json`.
## Current reviewer considerations

Source SHA-256: `dd3b39acd1b427b0b31539754099ae6c769885e22e204bfa5c58c90d6b897d0f`.

# Decisions for review `review-4359053bb00444e6`

## D1 — Preserve the selected canonical rule and valid-input distribution

**Input choice.** Keep generator version `3.0.0`, the three production scene profiles, and canonical Racket `RULE_HASH = 6868d528f0b2` unchanged.

**Original rationale.** The prior retained review had already repaired the substantive singleton-object and teaching-distribution defects. The current before battery showed every stage except strict scalar lint green, so there was no measured reason to reopen rule semantics or sampling.

**Alternatives considered.** Rewrite the rule, change profile frequencies, or introduce the parametric variants into production. All were rejected: the first two were unsupported by current evidence, and the packet explicitly requires proposed variants to remain separate from canonical execution.

**Probes.** Before battery 11/12; after battery 12/12; canonical rule smoke and authority sync remained green. The final generator hash is `dd3b39acd1b427b0b31539754099ae6c769885e22e204bfa5c58c90d6b897d0f`.

**Failure modes and limits.** This choice inherits the existing intentional fixed-order lesson schedule and compact-object curriculum. It does not claim arbitrary query rotation or exhaustive rival coverage.

## D2 — Reject noncanonical public call scalars at the generator boundary

**Input choice.** Require `type(seed) is int`, `type(sample_index) is int`, `sample_index >= 0`, and difficulty in `{None, "easy", "medium", "hard"}`.

**Original rationale.** Unknown; the baseline had no explicit validation for these call arguments. Python's Boolean-as-integer relationship and permissive context handling allowed malformed values to be accepted silently.

**Alternatives considered.** Coerce strings/floats to integers, validate inside `gen_ctx`, or suppress the linter warning. Coercion hides caller errors, a shared-runtime change exceeds task scope, and suppression would leave reproducible malformed calls accepted. A local fail-fast validator is the smallest root-cause repair.

**Probes.** The test was red first: 7 invalid cases were accepted and 4 already rejected. After the repair, all 11 cases reject, the 34-test focused suite passes, and strict defect lint is green.

**Failure modes and limits.** This intentionally rejects callers that relied on coercion. Valid calls are unchanged; the task-local validator does not establish a shared policy for other generators.

## D3 — Use `period` as the first parametric rule dimension

**Input choice.** Support bounded values `period in {2,3}`, where selected component indices satisfy `i % period == phase`; canonical default is 3.

**Original rationale.** The canonical rule already expresses a periodic component schedule (`0,3,6,...`). Changing the small period preserves the original reasoning sequence—find components, sort left-to-right, select a periodic subsequence, recolor whole objects—while changing actual outputs.

**Alternatives considered.** Output-color variation, object-order direction, or arbitrary period values. Output color is less reasoning-rich; reversing order introduces a second structural change; unbounded periods produce weak or empty selections. `{2,3}` is the smallest nearby, observable family.

**Probes.** Complete Racket programs for periods 2 and 3 were executed. For every retained episode, period rivals differ on all three demonstrations and the query.

**Failure modes and limits.** Evidence covers the four retained episodes and selected generator inputs, not every seed or every possible component count. The prototype rejects unsupported values rather than extrapolating.

## D4 — Use `phase` as the second parametric rule dimension

**Input choice.** Support `phase in {0,1}` for both allowed periods; canonical default is 0.

**Original rationale.** Phase changes which ordered components are selected without changing object roles, geometry, or ordering. It is a direct nearby rival already relevant to the production semantic contract.

**Alternatives considered.** Permit every mathematical phase or use a random offset per example. Full phase domains add settings with less support, and per-example resampling violates the episode-level hidden-rule requirement. The bounded two-phase choice is sufficient to test inference of the schedule.

**Probes.** Each phase has an exact Racket source and complete episode. Every alternate phase/period setting disagrees on demonstration indices 0, 1, and 2 before the query.

**Failure modes and limits.** The public input does not encode phase; identifiability depends on demonstrations. The prototype therefore must not emit an episode whose demonstrations fail the retained rival checks.

## D5 — Choose one parameter setting per episode, with three demonstrations

**Input choice.** Fix `(period, phase)` once using the episode seed and use that same setting for three demonstrations plus one query. Public artifacts omit the hidden setting and query output.

**Original rationale.** `PARAMETRIC-RULES.md` requires episode-level consistency and demonstration-level distinction. Three demonstrations also match the production task's established lesson length.

**Alternatives considered.** Resample settings per pair, expose the parameter in the grid, or use one demonstration. Per-pair resampling makes the lesson internally inconsistent; explicit encoding changes the puzzle; one demonstration is more fragile and unnecessary.

**Probes.** `checks/parametric/selection-schedule/summary.json` binds seeds 8730–8733, source hashes, three demonstrations, one query, and every pairwise distinction. The task tests verify exact canonical default text and whole-component behavior.

**Failure modes and limits.** The retained four episodes are bounded evidence, not a broad distribution census or training approval. Production APIs remain fixed-rule.

## D6 — Keep the production curriculum ordered; report rotation ambiguity rather than hide it

**Input choice.** Treat the intended assembly as three ordered demonstrations followed by the query. Run arbitrary query rotations as a diagnostic, not as an advertised capability.

**Original rationale.** The generator's deterministic profile cycle was deliberately designed so every consecutive production window contains `canonical_zigzag`, `shape_mix`, and `row_order_trap`. No declaration says downstream may permute the query among those four pairs.

**Alternatives considered.** Claim rotation support from the 12-lesson smoke test, ignore rotation testing, or redesign the profile schedule. The first is false, the second violates the requested census, and the third is a substantive curriculum redesign unsupported by the current assignment. The correct choice is to retain the failure and state the boundary.

**Probes.** A 300-lesson census had 0/300 production ambiguities. Required rotation found 15/1,200 ambiguities, all involving `row_major_third` when demonstrations omit `row_order_trap`; the diagnostic-policy rerun preserved those counts and exited successfully for the declared ordered policy.

**Failure modes and limits.** Any consumer that rotates queries can create a teaching defect. Such consumers must add a witness, increase demonstrations, or resample; this return does not solve arbitrary rotation.

## D7 — Leave both adversarial audit targets unchanged

**Input choice.** Record source-bound findings for `e71a5fe2abc2` and `666934e5ac80` without editing either generator.

**Original rationale.** Audit duty requests inspection, evidence, and a finding—not repair. The assignment permits edits only to the selected task.

**Alternatives considered.** Patch the obvious defects while present or omit checks because prior audits existed. Both were rejected: cross-task edits violate scope, and retained historical findings are not measurements of current bytes.

**Probes.** `e71a5fe2abc2` received a full strict audit battery plus a 30-sample marker probe and Racket application. `666934e5ac80` received fresh portable task-test and strict semantic-gate runs.

**Failure modes and limits.** The audit findings do not prove there are no additional defects, and no audit target is approved or repaired by this return.

## Native parametric build — review-9b9444e5e15d6661

- Built a native episode-fixed `(period, phase)` family with settings
  `(2,0)`, `(2,1)`, `(3,0)`, and `(3,1)`. The default `(3,0)` source is the
  byte-exact selected canonical program.
- The invariant reasoning is: discover non-background 4-connected objects,
  order them left-to-right, then recolor whole objects occupying schedule
  positions `i mod period = phase`. Inputs are matched across settings and
  support independently requested 2–6 demonstrations and 1–4 queries.
- The ordinary lesson bank contains row-order traps and a dense 30x30 query.
  A bounded four-seed audit covered 48 jobs and found zero surviving
  wrong-order or anchor-only rivals. Query source position is shuffled while
  prefixes remain stable.
- Protected native qualification passed four settings, two seeds, three
  demonstrations and four queries per job: 128 Racket evaluations. The
  source-bound witness replays a wrong-order counterfactual on the 30x30 case.
  Public projection and first-turn privacy checks also pass.
- Evidence is finite and reviewer-reported. It does not exhaust arbitrary
  programs, measure learning gain, accept the exact source, or admit training;
  those remain owner-side gates.
