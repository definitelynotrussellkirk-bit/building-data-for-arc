# Working notes: 14dacb3b518f

## 2026-10-03 repair

Baseline generator `2.1.1` had four blocking battery stages:

- no `RULE_HASH` pin;
- `self_check` accepted all destructive mutations and minimal impostors;
- dead/singleton pseudo-axes plus degenerate textures mixed into the ordinary domain;
- overrides were not exact across difficulty bands, dimensions were ignored by degenerates, and unknown keys were accepted.

The prose also described exactly one frame plus one 2×2 solid while code actually attempted 1–3 of each with capped rejection loops. More importantly, every positive was a rectangular frame and every negative had size at most 6, preserving strong shortcuts that fit all five canonical pairs.

### Chosen repair

- Keep the canonical Racket authority unchanged and pin hash `fe78a969401a`.
- Replace rejection placement with four separated constructive slots.
- Advertise only four exact, observable axes: height, width, holed count, solid count.
- Use a five-profile schedule (length 5 is coprime to the common `seed == sample_index` census) with canonical dimension anchors in every band.
- Add non-frame one-hole pockets, a two-hole connected shape, leaky C near-misses, and large hole-free rectangles.
- Add an executable structural mirror, semantic witnesses/rivals, lesson-identifiability check, task-local mutation fixtures, and regression tests.
- Add `workspace/lesson_probe.py`, which dynamically reads the final module's rival declarations and audits 100 lessons per band over every cyclic schedule start.

### Remaining limits

The generator intentionally stays inside one foreground color and 1–2 objects per topology class. The lesson probe establishes coverage against declared rivals for this deterministic curriculum; it does not prove universal induction or enumerate every imaginable shortcut.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `60d817465de0aa5552e054895a50a584f2f4f4aaac5a99057dea7bb50b929121`.

# Decisions for `14dacb3b518f`

The original author rationale is not retained beyond the baseline code and prose. Where noted below, the “original rationale” is therefore **unknown**; observations about the old design are code-level inferences, not claims about author intent.

## D1 — Keep the canonical authority unchanged

- **Choice:** Pin `RULE_HASH = "fe78a969401a"` and make the Python generator/mirror conform to the selected canonical Racket rule.
- **Original rationale:** Unknown. The baseline omitted the required pin although its generated outputs were broadly compatible with the canonical rule.
- **Alternative rejected:** Edit the Racket rule to match generator quirks. That would change authority without evidence of a canonical defect and would not solve the distribution or contract failures.
- **Probe:** Canonical parity is tested over all five usable pairs; final `rule_smoke`, `racket_lint`, and `authority_sync` are green.
- **Limitation:** An archival solution-bank raw-code record remains divergent, as reported by authority sync, but selected execution parity passes.

## D2 — Make enclosed-hole topology the only labeling primitive

- **Choice:** Analyze each 4-connected color-6 component, count background regions inside its bounding box that do not touch that box boundary, recolor components with at least one such region to `8`, and all others to `2`.
- **Original rationale:** The baseline prose described frames and solids rather than a robust topology implementation. Whether that simplification was intentional is unknown.
- **Alternatives rejected:** “Rectangular frame,” “has any bounding-box gap,” “component size,” and rank-based implementations. All are canonical-fitting shortcuts, not the intended invariant.
- **Probe:** `test_rule_mirror_recolors_each_component_by_enclosed_hole_count`, canonical parity, semantic rivals, and the Racket-bound counterexample under `checks/question_shortcut/`.
- **Failure mode controlled:** A leaky C has empty cells inside its bounding box but no enclosed hole; a filled pocket can have a hole without being a thin frame.

## D3 — Replace pseudo-axes with four exact observable axes

- **Choice:** Expose `grid_h=10..14`, `grid_w=12..16`, `n_holed=1..2`, and `n_solid=1..2`. Reject unknown overrides and invalid difficulties.
- **Original rationale:** Unknown. The baseline exposed singleton/dead metadata axes and texture controls whose ordinary and degenerate behavior overlapped.
- **Alternatives rejected:** Keep `palette_size`, `position_bias`, `n_distinct_colors`, `density`, palette aliases, and degenerate textures. Those values either could not change the grid, were silently ignored, or bypassed dimension controls.
- **Probe:** Boundary-cross-product regression over all three bands and the battery override stage. Final result: 7,740 accepted draws, 86 cases, zero findings; unknown keys are rejected.
- **Limitation:** The narrow color vocabulary is deliberate. Palette diversity would add complexity without teaching the rule.

## D4 — Use constructive four-slot placement

- **Choice:** Partition every legal grid into four separated corner slots, shuffle slot assignment, then paint one component per requested slot.
- **Original rationale:** The baseline used capped random placement; its rationale is unknown.
- **Alternatives rejected:** More rejection sampling or silently reducing requested counts. Both make exact overrides probabilistic and can bias shapes toward easy-to-place cases.
- **Probe:** Every generated grid is re-analyzed before return; observed dimensions and object counts must exactly equal requested values. Boundary override tests cover 48 combinations per band.
- **Failure mode controlled:** No overlap, no accidental 4-connectivity between objects, and no “best effort” count shortfall.

## D5 — Add topology-preserving adversarial shape families

- **Choice:** Positive families are thin frames, non-frame filled pockets, and a connected two-hole object. Negative families include leaky C shapes, large rectangles, L shapes, pluses, lines, and smaller rectangles.
- **Original rationale:** Unknown. Baseline positives were all thin frames and negatives were at most size 6.
- **Alternatives rejected:** Merely vary frame dimensions or add more small solids. Those changes leave size, frame, exact-one-hole, and rank shortcuts intact.
- **Probe:** Four semantic witnesses explicitly bind to five rivals. The exact seed-0/sample-0 scene includes a size-20 solid, a size-13 leaky C, a size-13 non-frame one-hole object, and a size-10 frame.
- **Limitation:** This is a focused teaching vocabulary, not an exhaustive topology generator.

## D6 — Use a deterministic five-profile curriculum with canonical anchors

- **Choice:** Select profile `(seed + sample_index) mod 5`. Each band contains canonical-sized anchors and linked shape/count combinations; five is coprime to the common seed-equals-sample-index probe cadence.
- **Original rationale:** Unknown. The old generator did not provide an executable lesson schedule.
- **Alternatives rejected:** Pure independent random sampling, because a finite lesson can miss the sole shortcut-refuting case; a fixed one-profile cycle, because it reduces variety and profile-floor support.
- **Probe:** `workspace/lesson_probe.py` forces all five cyclic starts. In 100 lessons per band, each start appears 20 times, every declared rival is contradicted by at least one demonstration in every lesson, and 1,479 of 1,500 draws are unique.
- **Limitation:** The deterministic curriculum establishes coverage for declared competitors, not universal induction.

## D7 — Make malformed-scene rejection part of the public contract

- **Choice:** `self_check` validates rectangular integer grids, exact input colors, dimension range, 2–4 separated components, and both topology classes in their declared count range. Task-local mutation fixtures cover blank, one-class-only, wrong-color, extra-component, out-of-range, and ragged scenes.
- **Original rationale:** The baseline `self_check` effectively returned acceptance for almost everything; rationale unknown.
- **Alternatives rejected:** Acceptance-only validation or checking only colors/dimensions. Those tests cannot detect semantic drift or malformed examples.
- **Probe:** Before: 0/56 destructive mutations rejected. After: battery reports 51/60 rejected, including all absent-color, blank, and foreground/background inversions; task-local malformed fixtures and minimal impostors all reject.
- **Limitation:** Some generic duplicate-first-row mutations remain lawful task instances, so rejecting 60/60 would be an incorrect target.

## D8 — Bind semantic claims to executable rivals and a reusable probe

- **Choice:** Declare `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable`. Add `workspace/lesson_probe.py`, which imports these declarations from the final source rather than copying a rival-name list.
- **Original rationale:** No semantic contract existed.
- **Alternatives rejected:** Rely solely on the battery’s small lesson smoke sample or document rivals only in prose.
- **Probe:** The tool verifies every canonical shortcut against all five canonical pairs, checks 300 complete lessons, tests all cyclic starts, records unique-input counts, and reports harmful ambiguity separately from query disagreement.
- **Limitation:** Undeclared rivals remain outside the probe; this is stated in the JSON report.

## D9 — Preserve honest solve evidence

- **Choice:** Keep the blind solve’s genuine failed first revision and mark the post-repair solve as exposed.
- **Original rationale:** Required by the review protocol.
- **Alternative rejected:** Manufacture a failure or call the post-repair solve blind.
- **Probe:** `solve-blind/summary.json` records two attempts and no earlier exposure; `solve/summary.json` records one attempt and earlier exposure `yes`.

## 2026-10-24 native parametric admission candidate

The retained native family is under `workspace/parametric/`. Its exact canonical default is `rule_mode=hole_presence`, whose Racket bytes hash to `fe78a969401a4f718a8537ef8ea1a2a748a34cd2a3a8bcdd28b964d1654b1f9d`. The alternative `rule_mode=most_holed_size_threshold` first selects the unique component with the most enclosed holes, binds that component's occupied-cell count as `anchor_size`, then recolors every component by whether its size is at least that input-derived threshold. Its program hash is `8680e4030bf7e4d61eeb18491c9906437661209cf2da469251c96fd892b4c6eb`.

The first four-object sampler made the alternative collapse to “paint the two largest objects.” I replaced it with five components: a unique two-hole anchor, a one-hole object and a leaky bbox-gap distractor whose sizes cross the anchor threshold across demonstrations, plus large and small solids. Protected-Racket teaching evidence now rejects both the two-largest and any-bbox-gap rivals in visible demonstrations. The sampler sweep covered 1,280 episodes (32 seeds, both settings, demos 2–6, queries 1–4) with zero construction/parity/privacy/count failures, including a substantive 30×30 case.

Native qualification at `checks/14dacb3b518f/qualification/qualification.json` passed four protected-Racket jobs (both settings, seeds 0 and 17, four queries each); sibling execution evidence is retained. The source-bound sequential witness uses a 30×30 alternative-setting query: changing `anchor_size` from 39 to 40 changes 39 output cells. The candidate is reviewer-ready only. Exact-source owner acceptance and any training admission remain pending.

Limits: the teaching audit covers the named two-largest and bbox-gap rivals, not every possible rule; the causal witness is one bounded executed case. No production generator or canonical rule bytes were changed by this parametric addition.

## Current reconciled parametric family

Three rules are native-qualified and accepted on the current exact source: canonical hole_presence, most_holed_size_threshold, and min_holes_2. Both original accepted programs/samplers and the incoming threshold-two branch remain exact. The duplicate canonical setting is counted once. All three programs were checked for demo-only identification on both branch samplers, with no grammar guard. See `evidence/owner-variant-reconciliation/current.json` and `parametric/accepted.json`. Existing production source, canonical rule, audit status and training admission remain separate.
