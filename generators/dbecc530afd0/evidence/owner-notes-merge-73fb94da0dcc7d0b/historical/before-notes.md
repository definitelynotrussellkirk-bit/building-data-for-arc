# Working notes: dbecc530afd0

## Current selected account (review-be34719285507965)

- **Intended rule:** color 4 marks the corners of one or two complete axis-aligned rectangles; copy the grid and paint each rectangle's strict interior color 2. Extra yellow cells are permitted only when they do not create an additional rectangle.
- **Selected source:** generator version `3.0.0`, SHA-256 `4618d193dbd680fe48516a9f1968555824e50a7d1d35bb723bdd31f51ef17e02`, canonical `RULE_HASH=bd0dec43bf33`.
- **Domain:** rectangular integer grids with colors 0 and 4, exactly 1–2 detected rectangles, no shared rectangle corner, and at most 3 non-corner yellow cells. Public call scalars and advertised axes are strict; diagnostic textures are no longer ordinary lawful draws.
- **Lesson schedule:** period 4, alternating `canonical_anchor` and `interleaved_rectangles`. A lesson uses 3 demonstrations plus 1 query. Every 3-of-4 query rotation retains an interleaved witness against `adjacent_equal_row_pairs_only`.
- **Canonical support:** default anchors remain 10×10/two-color and preserve the canonical-fitting shortcut, but their rectangle geometry varies across seeds. Final profile-floor evidence is exact/envelope 34/60, with easy 9/20, medium 11/20, hard 14/20.
- **Retained failures:** the baseline validator accepted a three-rectangle input; the first repaired source then failed the diversity gate because sample index 0 collapsed to four official grids. Both are covered by focused regressions.
- **Authority decision:** canonical semantics and normalized rule hash did not change. Only the selected nested and top-level `target_code` fields were synchronized to the canonical exact source; both archival `raw_code` copies and all unrelated decoded values were preserved.
- **Proposed extension (not selected):** `workspace/parametric/prototype.py` varies `inset_depth ∈ {1,2}` once per episode. Depth 1 is exact canonical behavior; depth 2 paints only cells at least two steps inside. Two Racket-backed episodes and all 8 query rotations distinguish the settings.

## Evidence and limits

- Final battery: `checks/after-final/` — 12/12 stages green on the selected source.
- Portable task tests: `checks/task-tests-final/` — 79/79 passed.
- Production census: `checks/lesson-census-final.json` — 300/300 lessons, 1,200 pairs, 1,200 query rotations, 1,009 unique inputs, zero ambiguity against the declared rival.
- Fixed-seed schedule census: `checks/after-final/checks/dbecc530afd0_after_semantic_gate.schedule-census.json` — all 4 starts × 3 bands × 4 query positions, 48/48 rotations unambiguous.
- Exact shortcut witness: `counterexamples/review-be34719285507965-v0001/interleaved-shortcut.json`.
- Parametric evidence: `checks/parametric/inset-depth-v1/report.json`.

These are finite checks against one declared canonical shortcut and one proposed depth counterfactual. They do not prove unique induction against every possible human or model hypothesis, and the proposed depth-2 rule has no production approval.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.


## Current external prototype follow-up

The writer uses fixed public/episode-001.json and episode-002.json ordinals for consecutive seed-selected depths; public names therefore encode setting order. It hardcodes three demonstrations and one query; rotations are not simultaneous four-query evidence. The exact reviewer program remains unchanged and unapproved. External work must use visible-content public identifiers and independent demo/query counts, then exercise four queries through Racket with focused privacy/count checks. Source-bound pending work: `generators/dbecc530afd0/evidence/parametric-external-followup-be34719285507965/manifest.json`. Owner inspection was static; reported batteries were not rerun.
## Current reviewer considerations

Source SHA-256: `4618d193dbd680fe48516a9f1968555824e50a7d1d35bb723bdd31f51ef17e02`.

# Decisions: dbecc530afd0

## D1 — Keep the canonical reasoning pattern fixed

**Choice.** Preserve “find one or two axis-aligned rectangles from four yellow corners and fill each strict interior red.” Keep `RULE_HASH=bd0dec43bf33` and the canonical ledger unchanged.

**Rationale.** All 8 canonical labels and the original-family role structure agree. The defects were distribution, validator, teaching, and exact selected-source synchronization—not rule semantics.

**Rejected alternatives.** Changing the output color, filling borders, using only one rectangle, or pairing yellow rows greedily would alter the task. The adjacent-row interpretation was retained only as an executable rival.

## D2 — Narrow the lawful domain to the advertised grammar

**Choice.** Accept rectangular 0/4 grids with exactly 1–2 complete rectangles, no shared corner, and at most 3 yellow cells that are not rectangle corners. Reject diagnostic textures, all-one-color impostors, booleans/floats/strings for integer controls, negative sample indices, unknown axes, and incompatible overrides.

**Prior choice.** The baseline generator exposed diagnostic modes as ordinary textures and `self_check` accepted the retained three-rectangle input.

**Reason for reversal.** Those inputs widened the validator beyond generation and beyond the task's stated object count. Baseline defect lint also found 138 loose scalar acceptances.

**Probe/failure mode.** `three_rectangle_counterexample()` now fails validation; all canonical pairs and generated defaults remain valid. The limit of three extras is task-local and intentionally conservative; inputs with more unrelated yellows remain outside the selected domain even when the Racket program could execute them.

## D3 — Use a four-slot teaching schedule

**Choice.** `SCHEDULE_PROFILES = (canonical_anchor, interleaved_rectangles, canonical_anchor, interleaved_rectangles)` with 3 demos + 1 query.

**Rationale.** Canonical examples all fit `adjacent_equal_row_pairs_only`. With two witness slots, every 3-of-4 demonstration set retains at least one exact refutation, independent of which pair is the query.

**Rejected alternatives.** A single witness in a four-pair window fails when that witness is held out. Random witness frequency does not guarantee lesson-level coverage. Making every draw a witness would lose canonical-profile anchors and overstate distance from the source family.

**Evidence.** Fixed seed 0 covers all 4 starts × 3 bands × 4 query positions; random census covers 300 lessons and 1,200 rotations. Both are finite checks against the declared rival only.

## D4 — Preserve anchors but vary their geometry

**Choice.** Canonical-anchor slots remain 10×10 with colors `{0,4}`, one or two rectangles, and a row ordering on which the adjacent-row rival agrees with the intended rule. Some seeds replay official canonical inputs; others construct new legal anchors.

**Prior choice.** The first repair sampled only the four official grids for sample index 0.

**Reason for reversal.** The strict self-check found only 4 unique grids across 40 seeds. A new failing regression required at least 5; the final implementation produces 30/40 without turning anchors into rival witnesses.

**Alternatives.** Adding noise would risk accidental rectangles and weaken the anchor role. Enlarging all anchors would reduce exact canonical-profile support. Constructive rectangle variation preserves both.

## D5 — Exact overrides bypass curriculum scheduling

**Choice.** When all advertised axes are explicitly supplied, honor them directly rather than forcing the scheduled profile.

**Rationale.** Overrides are an API contract and test surface; a curriculum profile should not silently rewrite requested dimensions, rectangle count, extras, bias, or texture.

**Failure mode.** Partial or incompatible requests raise an explicit conflict instead of silently adapting. This means override-generated examples are not guaranteed to carry the lesson witness; production lessons use unoverridden sampling.

## D6 — Synchronize selected authority fields, preserve archival raw code

**Choice.** Replace only `/racket_target/target_code` and `/target_code` in the two selected original-family JSON files with canonical exact source. Preserve both `raw_code` copies and every unrelated decoded value.

**Rationale.** Execution parity already held, but active selected authority text was not exact canonical source. The generic helper's whole-text key-count check could not safely patch files containing both nested and top-level target fields, so a task-local JSON-pointer-aware synchronizer and receipt were built.

**Limit.** This is formatting/source synchronization, not a semantic Racket change. The canonical ledger was not touched.

## D7 — Prototype one small rule parameter, separately

**Choice.** Proposed `inset_depth ∈ {1,2}` selected once per episode. Depth 1 is canonical; depth 2 erodes the painted interior by one additional cell from every boundary. Detection, object roles, input grammar, output color, and composition are unchanged.

**Why suitable.** It changes a single meaningful action parameter while preserving the original rectangle reasoning. Large enough rectangles yield visibly distinct labels, and each demonstration can distinguish the setting.

**Rejected alternatives.** Varying rectangle count is an input parameter, not a rule parameter. Varying output color changes a fixed semantic role. Choosing depth per rectangle or per example would make the episode internally inconsistent.

**Limit.** Only settings 1 and 2, two seeds, a bounded sampler, and the opposite-setting rival were checked. The prototype is proposed, not selected or approved.

## D8 — Stop after one post-repair solve revision

The visible examples directly supported the full four-corner rule, including an interleaved two-rectangle example. One implementation passed 3/3 visible examples. Additional revisions would have been manufactured rather than evidence-driven; prior exposure was declared `yes` and reference consultation during the solve `no`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/dbecc530afd0/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
