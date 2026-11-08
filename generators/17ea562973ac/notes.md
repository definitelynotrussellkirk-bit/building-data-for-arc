# Working notes: 17ea562973ac

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current opt-in parametric family

`workspace/parametric/adapter.py` adds private episode-fixed `peel_depth=0|1`.
Depth zero is the exact canonical Racket source. Depth one computes the outer
marker box, removes all markers on its perimeter, then recomputes the box of
the surviving strict-interior markers. Independently varying gaps and noncorner
outer extrema distinguish this from geometric inset or coordinatewise rank
trimming. The production source, approval and conservative domain below remain
unchanged; the prototype separately extends canvases to 30×30 and density to
4–160 markers, requiring at least two survivors spanning a 4×4 box.

Two constructive demos distinguish the declared rules and shortcuts: a
noncorner-extrema scene with an interior survivor that must clear, followed by
exactly two survivors. Omitting the second demo leaves a concrete
`requires_three_survivors` shortcut; `tests/test_parametric.py` retains that
minimal regression. Default use is three demos, supported counts are 2–6 demos
and 1–4 distinct queries. A fixed four-query schedule includes 6×7, 12×16,
22×26 and substantive dense 30×30 scenes. Input RNGs are independent of settings
and requested query count. The public projection reveals one query at a time.

Current source-bound focused evidence is in
`workspace/parametric/evidence/current/`; its inventory is
`workspace/parametric/evidence/manifest.json`. The reusable `verify.py` executes
both parameter rules, private labels, teaching witnesses and public projections
through the supported runtime. See its README for exact commands. Qualification
and causal witness are reviewer evidence; owner integration followed by fresh
native qualification/acceptance is the next action. Finite rivals do not prove
universal identifiability, and this work makes no training-admission claim.

## Current reviewer considerations

Source SHA-256: `05d0b41e19145209728e54f911ed19f9448e168b198992f1a912c976f22d10ee`.

# Decisions for `17ea562973ac`

The baseline implementation, prose, public controls, and validator contradicted one another, so its original design intent cannot be recovered reliably. Where the rationale below is marked **unknown**, the replacement is derived from the selected canonical rule, all five canonical pairs, and measured teaching failures rather than an invented explanation of the old code.

## D1 — Keep the selected rule; repair the generator around it

**Choice.** Preserve rule hash `22bfb52d3f48`: find every cell of the one nonzero color, compute their minimal bounding rectangle, and return a fresh zero grid containing only that rectangle's border in the same color.

**Original rationale.** The selected canonical/raw Racket sources and all five labels agree on this behavior. The baseline generator's conflicting “two diagonal cells” description has no trustworthy rationale.

**Alternatives considered.** (a) Change the rule to match the baseline's two-cell prose; rejected because it would contradict canonical examples with three or four markers. (b) Keep the baseline sampler and only update prose; rejected because it still accepted invalid scenes, exposed dead controls, and failed to teach a canonical-fitting count shortcut.

**Probes.** Canonical 5/5 ownership in `tests/test_generator.py`; 120/120 selected-Racket mirror parity in `checks/after/checks/17ea562973ac_after_rule_smoke.json`; independent oracle comparison in `checks/focused_audit_final.json`.

**Failure modes and limits.** The Python mirror is diagnostic rather than authority. The selected Racket program remains authoritative, and finite generated probes do not establish behavior outside the declared authoring domain.

## D2 — Use one explicit, conservative input grammar

**Choice.** Lawful generated inputs are rectangular zero-background grids of 6–12 rows by 7–14 columns, with exactly 2–8 markers of one color from 2–9; the marker bounding box must span at least 4 rows and 4 columns.

**Original rationale.** Unknown. The baseline stated “exactly two” while emitting roughly 4–9 cells and did not enforce a coherent domain.

**Alternatives considered.** (a) Admit arbitrary ARC sizes/colors/counts; rejected because the repair needs a testable training domain supported by canonical profiles, not an unmeasured claim about the full mathematical rule. (b) Restrict to exactly two markers; rejected because it excludes canonical inputs and preserves the strongest canonical shortcut. (c) Permit color 1 or marker counts above 8; mathematically plausible, but rejected from this authoring version because neither is needed for canonical/profile support and both would widen the claimed domain without corresponding evidence.

**Probes.** Strict mutation tests, malformed-grid diagnostics, canonical acceptance, and 600 independent generated scenes in `checks/focused_audit_final.json`.

**Failure modes and limits.** This is a deliberate curriculum domain, not a statement that the abstract rule fails for smaller/larger grids, color 1, or more markers. Those cases remain untested extrapolation.

## D3 — Expose only four exact public axes

**Choice.** The live public controls are `grid_h`, `grid_w`, `color`, and `num_cells`. Every declared legal value is directly recoverable from emitted pixels, works in every difficulty band, and invalid or unknown values raise.

**Original rationale.** Unknown. Baseline metadata advertised controls that were dead, overlapping, or not exact; unknown keys were silently accepted.

**Alternatives considered.** (a) Keep texture/motif controls and reinterpret them; rejected because their semantics were not observable or authority-backed. (b) Mark many combinations incompatible; rejected because constructive placement makes the full Cartesian product feasible. (c) Accept unknown keys for forward compatibility; rejected because typographical errors then silently change experiments.

**Probes.** The final override matrix ran 33,300 draws with zero findings or warnings and rejected an unknown key: `checks/after/checks/17ea562973ac_after_override_results.json`. Focused low/mid/high tests cover all bands.

**Failure modes and limits.** Exact controls constrain observable output facts only; they do not promise a particular bounding-box location or marker arrangement.

## D4 — Construct scenes rather than reject-sample them

**Choice.** Draw a valid bounding box first, place profile-defining markers that force its extrema, then add distinct markers from shuffled in-box candidates until the exact requested count is reached.

**Original rationale.** The baseline's placement rationale is unknown.

**Alternatives considered.** (a) Rejection sampling random cells until all constraints happen to hold; rejected because it obscures override guarantees, can become slow at boundaries, and makes coverage harder to reason about. (b) Place only bounding-box corners; rejected because it never teaches that interior markers are cleared or that all markers, not just the first two, define the box. (c) Put distractors outside the bounding box; rejected because every nonzero marker belongs to the same rule-defining set.

**Probes.** Exact override tests at minimum, midpoint, and maximum values; deterministic 2–8 count coverage; zero invalid scenes over 600 independent draws.

**Failure modes and limits.** Marker placement is intentionally constrained to the bounding rectangle. It does not model unrelated colored distractors because the selected rule and canonical examples do not establish how such distractors should be interpreted.

## D5 — Weight counts to teach the canonical shortcut

**Choice.** The default schedule is 50% two-marker, 25% three-marker, and 5% each for counts 4–8. Every four consecutive pairs contain two two-marker cases, one three-marker case, and one 4–8 case.

**Original rationale.** No defensible baseline distribution rationale was present.

**Alternatives considered.** (a) Uniform counts 2–8; rejected because a short three-demo lesson could omit the two-marker case that disproves the strongest canonical-fitting shortcut. (b) Use only two-marker cases; rejected because it would not teach interior-marker clearing, first-two insufficiency, or higher-count generalization. (c) Preserve the baseline's effective 4–9 range; rejected because it never refutes “only draw a frame when at least three markers exist.”

**Probes.** The 600-draw audit observed per band: 100 count-2, 50 count-3, and 10 each for counts 4–8. The 300-lesson census found no surviving declared rival in production or any hold-one-out query rotation.

**Failure modes and limits.** This is a teaching distribution, not an estimate of natural ARC frequency. It intentionally overrepresents semantic witnesses.

## D6 — Use a four-pair, rotation-safe lesson schedule

**Choice.** Lessons have three demonstrations and one query from consecutive schedule starts. Four profiles repeat in order: two diagonal TL→BR, an interior three-marker case, two diagonal TR→BL, and a distributed/interior case. Query rotation is required, so every one of the four pairs must be safe to hold out.

**Original rationale.** Unknown; the baseline declared no executable lesson contract.

**Alternatives considered.** (a) Ordered-only safety with one special query slot; rejected because downstream assembly can rotate the query and the return guide explicitly asks to distinguish those policies. (b) Two demonstrations; rejected because holding out one witness can leave a declared rival alive. (c) Four demonstrations plus query; unnecessary after the four-pair rotation census showed three demos suffice against the declared rivals.

**Probes.** `checks/lesson-census.json`: 300/300 materialized lessons, 0 production ambiguities, 0/1,200 ambiguous rotations, 1,176 unique inputs, no materialization/hook/scoring errors. Task tests also exhaust eight cyclic starts across all four query positions.

**Failure modes and limits.** Identifiability is only against the declared finite rival set. It is not a proof that no unenumerated program fits three examples.

## D7 — Declare concrete rivals and witnesses

**Choice.** The executable rivals are: `requires_three_markers`, `retain_original_markers`, and `first_two_markers_only`. Their witnesses are respectively a two-marker input, an interior marker that must disappear, and a later marker that expands the complete bounding box beyond the first two.

**Original rationale.** Unknown; baseline semantic checking was advisory because no rivals or witnesses were declared.

**Alternatives considered.** (a) Declare no rivals and rely on label correctness; rejected because individually correct pairs can still form an ambiguous lesson. (b) Add many speculative rivals without independent implementations; rejected because unverifiable names create false confidence. (c) Use only the shortcut named by the review question; rejected because the other two are simple, plausible and expose different teaching failures.

**Probes.** Independent implementations in `workspace/reference_probe.py`; 300 disagreements per rival in `checks/focused_audit_final.json`; canonical-fit test for `requires_three_markers`; rotated census.

**Failure modes and limits.** The rival set is deliberately small and interpretable. Undeclared shortcuts remain possible.

## D8 — Mix canonical-scale and generalized size profiles

**Choice.** Ten deterministic size profiles are scheduled: the five canonical input dimensions `(7,8)`, `(8,8)`, `(6,10)`, `(9,7)`, `(8,9)`, followed by `(10,11)`, `(11,13)`, `(12,14)`, `(6,14)`, `(12,7)`. Difficulty bands offset the schedule rather than changing validity.

**Original rationale.** The baseline's size distribution rationale is unknown.

**Alternatives considered.** (a) Canonical dimensions only; rejected because it gives weak scale generalization. (b) Fully random dimensions; rejected because it weakens reproducible profile-floor coverage. (c) Give each difficulty a disjoint domain; rejected because exact overrides should remain valid in every band and difficulty should not silently redefine grammar.

**Probes.** Canonical profile floor: 29 exact size/palette hits over 60 draws, with at least 7/20 in every band; override and distribution gates green.

**Failure modes and limits.** Difficulty is schedule offset, not a calibrated reasoning-difficulty metric.

## D9 — Normalize the comment-only authority fork, not the rule

**Choice.** Remove one extra comment from the selected archival `target_code` so it is byte-identical to canonical `program_solution` and archival `raw_code`.

**Original rationale.** The comment's origin is unknown. It did not affect execution.

**Alternatives considered.** (a) Leave the fork and document it; rejected because the authority-sync stage correctly treats multiple selected source texts as drift. (b) edit canonical source; rejected because canonical behavior was already correct and no rule change was intended. (c) change executable semantics; rejected.

**Probes.** Before/after authority reports under `checks/before/` and `checks/after/`; canonical train 4/4 and test 1/1 remain correct; rule hash remains `22bfb52d3f48`.

**Failure modes and limits.** The authority-set file hash changes even though behavior does not. `REVIEW.md` reports this explicitly so it cannot be mistaken for a semantic rule edit.

## D10 — Add independent, portable reviewer tooling

**Choice.** Add a task-local pytest suite, `workspace/reference_probe.py`, and `workspace/audit_generator.py`. Canonical discovery uses `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` instead of fixed parent counts.

**Original rationale.** No task-local regression or independent oracle existed.

**Alternatives considered.** (a) Test only production `rule_mirror`; rejected because an implementation and its tests could share the same mistake. (b) import private runner internals; rejected by the packet contract and poor portability. (c) compute repository roots with `Path(...).parents[N]`; initially attempted, then rejected after the final handoff review exposed the layout assumption.

**Probes.** Baseline replay failed 49/58 focused tests. Final source passed 58/58 directly, in isolated runtime, and after fresh extraction and patch application. The final audit tool runs from the documented task directory and uses an independent geometry implementation.

**Failure modes and limits.** The tools are task-local and intentionally encode this task's grammar/rivals; they are reusable by future agents reviewing this task, not generic ARC validators.
