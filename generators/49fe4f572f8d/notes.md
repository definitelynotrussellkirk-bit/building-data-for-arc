# Working notes: 49fe4f572f8d

## Current separate parametric extension

`workspace/parametric/` adds episode-fixed `mode=down` (the exact canonical
program) and `mode=settle_clear_once`: gravity, one simultaneous erase of
same-color four-connected components with at least three cells, then gravity.
A newly formed group is retained after that final settle. The selected production
source and canonical rule are unchanged.

Two constructive demonstrations distinguish the declared 5 default / 16 extended
rivals before any query is considered. Counts are independently 2–6 demos and
1–8 queries; the usual export is 3/4, with a one-query turn projection. The
separate grammar reaches substantive 30×30 scenes. Native qualification passed
for both settings at seeds 0 and 17; 32 focused tests passed, and two protected
wrong-order counterfactuals replayed. See `checks/49fe4f572f8d/qualification/`,
`checks/49fe4f572f8d/causal/`, and `checks/49fe4f572f8d/focused/private/report.json`
in the reviewer return. `workspace/parametric/verify.py` reproduces the bounded
label/finite-rival audit. This is reviewer-ready evidence; owner exact-source
acceptance and training admission have not been performed.

## 2026-10-02 review

The imported v2.0.1 generator produced valid moving examples, but it was not distribution- or contract-complete:

- no `RULE_HASH` pin;
- zero default draws matched any canonical linked profile;
- canonical palettes of 5–7 foreground colors were unreachable;
- eight advertised axes included ignored aliases, single-valued axes, and negative fixtures in the ordinary domain;
- unknown override names were silently accepted;
- `self_check` admitted singleton, short-line, solid-block, and other rule-hiding inputs; and
- no task-linked semantic contract identified or refuted plausible shortcuts.

Version 3.0.0 narrows the public surface to four exact, observable axes and uses a deterministic ten-slot curriculum. Even slots reproduce each canonical `(height, width, total-palette, cell-count, occupied-column-count)` profile. Odd slots construct counterexamples to key rivals: identity, reversed within-column order, freezing a column that touches the floor, capping gravity at three cells, and applying gravity only when all foreground colors are unique.

The canonical demonstrations themselves refute floor-freezing, but they do **not** refute either “at most three cells per column” or “all foreground colors must be unique.” Those two are recorded in `CANONICAL_SHORTCUTS`; generated deep-stack and repeated-color witnesses refute them.

The authoritative Racket rule was not changed. The Python gravity implementation is only a validation/witness mirror. The complete inherited after-battery passed all 12 stages, including Racket execution and authority parity.

## Deliberate limits

The reviewed distribution stays close to the canonical scale instead of exploring large dense grids. It rejects identity-only scenes and monochrome/order-hidden scenes because they weaken the lesson. Override requests remain exact even when they replace the scheduled profile, so a forced sample is lawful but is not guaranteed to retain the semantic role of its original curriculum slot.

## 2026-10-03 lesson-level review

Lead used: accepted return `review-f5516c8562917503:v0001`, whose integrated v3.0.0 source is the immutable baseline for this assignment. Its aggregate before-battery was fully green, but the source had no `LESSON_COMPETITORS` declaration or `lesson_identifiable` hook, so aggregate witness frequency did not establish that each complete five-demo lesson rejected the same shortcuts.

A source-bound census used the production `puzzle_generators.runner.run_one` path, the authoritative Racket rule, the profile-floor pinned seed recipe, sample-index stride 11, five demos plus one query, and 100 lessons in each difficulty band. Across 300 lessons / 1,800 unique inputs, the existing `freeze_bottom_supported_columns` rival survived all five demonstrations in 30 lessons and disagreed on every corresponding query. Candidate canonical-scope rivals also exposed gaps: `max_three_columns_only` survived 211 lessons (15 query-discriminating), `max_seven_cells_only` 51 (8), `canonical_shape_only` 19 (10), and `five_plus_colors_only` 23 (9). These are finite-census findings, not a claim of universal induction. See `checks/lesson-probe-before.json` in the review return.

Version 3.1.0 adds those scope rivals, a joint `beyond_canonical_scope` witness, and a lesson hook that rejects any five-demo lesson for which a declared competitor survives. Slots 1, 5, and 9 construct a 10×10, 10-cell, four-column, two-color boundary profile; their cyclic spacing ensures every five-slot window contains one. Supported, deep, and repeated/mixed slots are likewise scheduled within every five-slot window.

The first full production-sampler rerun found one remaining cap-three shortcut at hard seed `104871007183328`, sample index `880`: the deep slot weighted feasible cell counts but still passed the full 5–10 domain to the draw, so it could choose five cells over three columns. The repair restricts only ordinary deep/mixed teaching draws to counts `>= n_columns + 3`, constructively forcing a four-cell column. Public exact overrides still use the complete advertised domain.

Final source hash `9bc30ae28c68f39d0c4ffc35fbff1d4070135a0474f55d353c27dd4e38275f24` passed 300/300 production-sampled lessons, 1,800/1,800 unique inputs, all ten cyclic start residues (30 each), and zero surviving declared competitors. The complete 12-stage after-battery and all 13 selected-task tests passed. The authoritative Racket rule and its hash were unchanged.
## Current reviewer considerations

Source SHA-256: `9bc30ae28c68f39d0c4ffc35fbff1d4070135a0474f55d353c27dd4e38275f24`.

# Decisions — 49fe4f572f8d v3.1.0

## D1 / G1 — Treat the complete five-demo lesson as the unit of quality

**Original rationale:** v3.0.0 already generated valid, diverse inputs and had aggregate semantic witnesses. The inherited design implicitly assumed that frequent witnesses pooled across draws meant each assembled lesson was teachable.

**Probe:** a production-path census assembled 100 complete lessons per band with the real runner and Racket authority. The floor-freeze rival survived 30/300 complete demo sets despite the aggregate battery being green.

**Decision:** declare `LESSON_COMPETITORS` and implement `lesson_identifiable(demos, query)` over the actual five-demo unit. The hook validates pair structure, generator-domain legality, authoritative expected behavior mirrored in Python, and rival survival.

**Rejected alternatives:**

- Raising aggregate witness frequencies only: this can still cluster witnesses outside a particular lesson.
- Checking only the query: query discrimination is useful evidence but the learner sees only demonstrations; a lesson must reject the rival before the masked query.
- Hard-coding rival names in the probe: it would silently drift from the source contract.

**Failure modes / limits:** a declared rival can be incomplete, malformed, or unrealistic. Tests therefore require total callables, verify canonical shortcuts against every usable canonical pair, and record rival errors rather than treating them as refutations.

## D2 / G3 — Add canonical-scope rivals, not arbitrary transformations

**Original rationale:** the canonical examples occupy a narrow envelope: 5–7 cells, 2–3 columns, five shapes, and at least five foreground colors. A model can fit those pairs while learning “gravity only inside the observed envelope.”

**Alternatives considered:** generic random wrong functions; a large enumerated DSL; only the two inherited shortcuts (`cap_three`, `unique_colors`). Generic or lookup-table rivals are cheap to invent but weakly connected to model behavior. A DSL search would be broader but is unnecessary for this bounded repair.

**Decision:** add five simple, interpretable restrictions: maximum seven cells, maximum three columns, exact canonical profile, canonical shape, and at least five colors. Each is executable, total on the task domain, and independently checked to fit all five usable canonical pairs.

**Probe:** baseline lessons left four of these alive in 19–211 of 300 lessons. The exact-profile rival was already refuted, but keeping it in the contract protects that property from regression. Final lessons leave none alive.

**Failure modes / limits:** this list does not exhaust compositional shortcuts. It is a minimum falsifiable set, not a claim of completeness.

## D3 / G3 — Use three cyclic boundary slots (1, 5, 9)

**Original rationale:** `EXAMPLES_NEEDED=5`; therefore the relevant schedule property is every cyclic length-five window, not the full ten-slot aggregate. One or two boundary slots can leave a five-slot gap.

**Alternatives considered:** make every noncanonical slot a boundary example; randomize the boundary profile; expand lesson size. All-boundary slots would reduce diversity and canonical resemblance. Randomization would turn a guarantee back into a probability. Increasing lesson size changes the training contract.

**Decision:** place joint boundary examples at slots 1, 5, and 9. Their maximum cyclic gap is four, so every five-slot window contains one while the even slots continue covering all five canonical linked profiles.

**Chosen boundary profile:** 10×10, 10 cells, four occupied columns, two foreground colors. It simultaneously exceeds canonical shape/count/column scope and goes below the canonical color-count floor.

**Probe:** deterministic cyclic-window tests across bands and seeds, plus the production census. All ten start residues appeared exactly 30 times in the final 300 lessons.

**Failure modes / limits:** exact public overrides may replace the scheduled profile; such override-generated samples remain lawful but are not claimed to preserve the original slot’s teaching role.

## D4 / G2 — Convert deep-stack weighting into a constructive guarantee

**Original rationale:** v3.0.0 used heavy weights on feasible cell counts in deep/mixed slots. The initial repair preserved that pattern.

**Counterexample:** hard seed `104871007183328`, sample index `880`, selected five cells over three columns, so no column had four cells and `cap_three_cells_per_column` survived.

**Decision:** for ordinary deep/mixed teaching draws only, restrict the `n_cells` draw domain to values `>= n_columns + 3`. By pigeonhole, at least one occupied column must then contain four or more cells. The exact override path still accepts every advertised value 5–10.

**Rejected alternative:** retry until a deep stack appears. Rejection sampling adds hidden runtime variance and can obscure whether an exact override was honored.

**Failure modes / limits:** the construction guarantees depth, not a particular row layout. Separate self-check and rival tests validate the resulting scene.

## D5 — Keep the Racket authority unchanged

**Original rationale:** the canonical rule already correctly expresses independent downward gravity with order preservation. All detected defects were in lesson composition and source contracts, not rule semantics.

**Decision:** do not edit `repo/shared/data/canonical/puzzles.jsonl`; retain `RULE_HASH=c3638032481f`.

**Probe:** rule smoke, Racket lint, authority sync, canonical outputs, and post-repair solve all passed. The before/after battery authority-set hash is unchanged.

**Failure modes / limits:** the Python `_gravity_down` mirror could drift in a future edit. Authority and Racket-backed production sampling remain required.

## D6 / T1 — Build a reusable, source-bound lesson probe

**Original rationale:** the shared semantic gate is intentionally a small smoke test and its aggregate census does not record the complete evidence needed here.

**Decision:** add `workspace/lesson_probe.py`. It loads the selected generator from disk, hashes it, verifies the rule pin against canonical source, opens one persistent Racket bridge, calls the production runner, iterates the generator’s actual declarations, and emits machine-readable JSON.

**Alternatives considered:** a notebook, ad hoc in-memory generator calls, or copying private runner logic. Those would be less replayable or could diverge from production assembly.

**Probe:** task-local tests cover pinned seeds, analysis counts, rule-hash binding, and the runtime `scripts` namespace required by `rule_wrap`. The final real run covers 300 lessons.

**Failure modes / limits:** it uses private bridge-opening machinery because the current runtime lacks a small public API for persistent authoritative lesson materialization; this is called out in `FEEDBACK_TO_CODEX.md`.

## D7 — Preserve domain and public exact controls

**Original rationale:** the v3.0.0 surface was already intentionally narrow and exact: `grid_h`, `grid_w`, `n_cells`, `n_occupied_columns`.

**Decision:** do not add new public override axes for palette or scene type. Boundary palette size is an internal curriculum choice. Keep height 6–10, width 7–10, cells 5–10, columns 2–4, colors 2–7.

**Probe:** override stage passed; final census observed every value in those ranges. Task tests explicitly distinguish scheduled deep draws from exact overrides.

**Failure modes / limits:** users cannot force a semantic scene directly. This avoids promising an axis whose combinations would require incompatibility rules, but it makes targeted external generation less convenient.

## D8 — Use prior review only as a lead

The accepted `review-f5516c8562917503:v0001` explained the v3.0.0 intent and was used to identify likely rivals. Its claims were not treated as measurements of the assigned bytes. The immutable baseline hash was verified and all before measurements were rerun in this packet.
