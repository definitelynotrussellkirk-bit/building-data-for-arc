# Current notes: `952d011ee8be`

Generator version: `3.0.0`
Final generator SHA-256: `6a95f875df81153cb527dd5eb3332b5bdb4754f7e91fcc409fd0f0fdbc01a3a2`
Canonical rule hash: `0b4a544c9655`

## Intended rule

The first row contains a three-color legend in left-to-right order. Color-5 walls partition the body into chambers. Count color-1 dots in each chamber: counts 1, 2, and 3 select legend entries 1, 2, and 3, while count 0 selects the final legend entry. The selected Racket authority paints the entire chamber, including its dots.

## Baseline defects reproduced

- `self_check` required the legend at columns 1..3 even though all five canonical inputs place it at columns 0..2; the baseline therefore rejected 5/5 canonical inputs.
- The sampler fixed one 3-column legend position and three vertical chambers, generated only counts 1..3, omitted a zero-dot case, and left a fixed-column shortcut viable.
- The prose incorrectly said dots remain unchanged, while the selected authority overwrites them.
- `RULE_HASH` was missing; declared texture/axis metadata was stale or dead.
- Initial repair iterations additionally exposed one-to-one scheduled-axis locks, byte-identical difficulty bands, and a wrong `schedule_profile` hook signature. Each now has a regression test.

The interrupted before battery and the initial 31-test red run are retained under `checks/before/` and `checks/tests-red-initial.log`.

## Final construction

Every default input has two horizontal bands and four rectangular chambers. Their dot counts are a permutation of 0, 1, 2, and 3, so one example exercises the complete lookup. Defaults vary:

- dimensions 11..15 by 10..16, including canonical-size anchors;
- legend offset 0..2 and all six legend permutations through exact overrides;
- one to three chambers in the upper band, independently varied split row;
- four scheduled count permutations, decoupled from the other exact axes;
- legal palettes, with difficulty-specific rotations so bands are not aliases.

The validator also accepts the selected canonical three- and four-chamber grammar. Exact public controls are `grid_h`, `grid_w`, `legend_offset`, `upper_chambers`, `split_offset`, `legend_order`, and `count_order`; all reject malformed or out-of-range requests.

## Semantic contract

Declared rivals cover:

- a legend hard-coded to columns 0..2;
- mapping zero dots to the first legend entry;
- preserving blue dots instead of overwriting them;
- assigning colors from chamber position instead of dot count.

The four corresponding witnesses are executable. Three demonstrations are required. Focused tests cover all query rotations over deterministic four-pair windows; the source-bound census found no ambiguity in 300 production lessons or 1,200 rotations against these rivals.

A minimal retained witness for the canonical fixed-column shortcut is `counterexamples/shifted_legend_shortcut.json`.

## Final evidence

- native after battery: 12/12 stages green with rotations required;
- focused portable task tests: 34/34 passed;
- self-check: 60/60 defaults clean, 5/5 canonical accepted, 60/60 destructive mutations rejected;
- rule smoke: 120/120 Racket applications and 120/120 mirror matches;
- exact overrides: 34,380/34,380 accepted draws across 382 cases and three bands;
- profile floor: 17/60 exact canonical-profile hits;
- semantic smoke: 600/600 strict draws, 12/12 lessons, 0/48 ambiguous rotations;
- large census: 300/300 lessons, 1,200/1,200 rotations, 1,200 unique inputs, zero ambiguity or execution errors.

## Authority and limits

No selected Racket authority or canonical example changed. The selected target is synchronized to canonical authority; one archival `raw_code` source remains textually divergent but passed execution parity.

The positive sampler deliberately uses four chambers so every single example contains all four count cases. It does not generate every lawful wall topology accepted by the authority, and finite declared-rival checks do not prove uniqueness against every possible hypothesis. Catalog training approval remains a maintainer decision.
## Current reviewer considerations

Source SHA-256: `6a95f875df81153cb527dd5eb3332b5bdb4754f7e91fcc409fd0f0fdbc01a3a2`.

# Decisions for `952d011ee8be`

## D1 — Preserve the selected Racket authority

**Choice.** Keep the selected canonical Racket rule and all canonical examples unchanged; pin `RULE_HASH = "0b4a544c9655"`.

**Rationale.** Rule smoke passed on the baseline, and direct inspection showed the generator/validator—not the transformation—caused the mismatch. The selected rule consistently fills the entire chamber, including dots.

**Rejected alternatives.** Editing Racket to preserve dots or moving the canonical legend to columns 1..3 would conform authority to a defective generator and contradict canonical outputs.

**Probe / limit.** Final authority sync and 120/120 Racket smoke applications passed. One archival `raw_code` is textually divergent but execution-equivalent on canonical pairs; it was not selected authority.

## D2 — Reconstruct the grammar from walls, not fixed columns

**Choice.** Parse 4-connected non-wall regions below the separator row and require rectangular chambers bounded by color 5. Accept three or four chambers in validation; generate four.

**Rationale.** Canonical inputs vary width and chamber count. Fixed vertical stripes rejected authority examples and invited coordinate shortcuts.

**Rejected alternatives.** Merely changing the expected legend columns while keeping three fixed stripes; generating arbitrary nonrectangular mazes. The first leaves the main distribution defect intact, and the second exceeds canonical evidence.

**Probe / limit.** All five canonical inputs pass. Generated positives use two horizontal bands and four rectangles; other lawful topologies remain outside the positive sampler.

## D3 — Put all four lookup cases in every generated example

**Choice.** Assign one chamber each of dot counts 0, 1, 2, and 3.

**Rationale.** The baseline never taught the zero-dot fallback. A complete per-example lookup reduces reliance on lesson ordering and gives every demonstration direct evidence for all outputs.

**Rejected alternatives.** Random independent counts or three chambers per draw. Either can omit a case, requiring fragile cross-example coverage.

**Probe / limit.** Focused tests inspect every generated chamber count. This choice fixes chamber count at four in production even though validation accepts canonical three-chamber scenes.

## D4 — Vary legend position and order explicitly

**Choice.** Expose exact `legend_offset` 0..2 and `legend_order` 0..5 controls, with shifted legends in the default schedule.

**Rationale.** All canonical legends happen to be at columns 0..2, so a hard-coded fixed-column rival fits every canonical pair. Shifted legends are the cheapest lawful counterexamples.

**Rejected alternatives.** Treat the canonical position as semantically fixed or vary colors without moving the legend. Neither refutes the coordinate shortcut.

**Probe / limit.** `counterexamples/shifted_legend_shortcut.json` is a minimal retained witness. The semantic gate observed the shifted-legend witness 386/600 times.

## D5 — Expose only exact, observable axes

**Choice.** Public controls are `grid_h`, `grid_w`, `legend_offset`, `upper_chambers`, `split_offset`, `legend_order`, and `count_order`.

**Rationale.** Every value can be reconstructed from returned pixels. Strict request validation makes failed or ignored controls visible rather than silently sampling something else.

**Rejected alternatives.** Preserve stale texture aliases or add hidden palette IDs that cannot be inferred from the grid.

**Probe / limit.** The native override matrix accepted 34,380/34,380 draws across 382 cases and rejected unknown keys. Only four of the 24 count permutations are default curriculum states, although all 24 are exact-override legal.

## D6 — Decouple default schedule axes

**Choice.** Use independent modular/block rotations for legend offset, band split, upper chamber count, legend order, and count order.

**Rationale.** The first repair used one shared four-slot schedule. Lint correctly showed that independently overridable axes were one-to-one locked, allowing one visible feature to predict another.

**Rejected alternatives.** Suppress the warning or add random jitter. Random jitter makes lesson coverage harder to reason about; an orthogonal finite schedule is inspectable and reproducible.

**Probe / limit.** Regression tests require complete pair support in the first 20 profiles and multiple counterpart values for each scheduled state. Finite schedules can still expose higher-order correlations not covered by these pairwise checks.

## D7 — Make difficulty bands real without changing semantics

**Choice.** Rotate the three legal legend colors through a seven-color role palette by difficulty while preserving geometry and exact axis values.

**Rationale.** Defect lint showed all three advertised bands were byte-identical. Palette rotation makes bands observably distinct without inventing a different rule.

**Rejected alternatives.** Remove difficulty support or make hard mode structurally invalid. Removing support would break the shared sampler contract; semantic changes by band would damage task consistency.

**Probe / limit.** A regression compares the same seed/index across all three bands. Difficulty currently changes palette, not reasoning complexity.

## D8 — Use executable rivals and require rotation-safe lessons

**Choice.** Declare four rivals: fixed legend columns, zero→first, preserve dots, and chamber-position lookup. Require three demonstrations and test every query position.

**Rationale.** Correct individual labels do not guarantee a teachable lesson. Executable rivals make ambiguity measurable rather than rhetorical.

**Rejected alternatives.** Narrative-only witness names or checking only the production query position. Both can report success while a hold-one-out lesson is ambiguous.

**Probe / limit.** Smoke evidence is 12 lessons and 48 rotations; the larger census is 300 lessons and 1,200 rotations with zero ambiguity. Undeclared rivals remain unknown.

## D9 — Fail closed in validation

**Choice.** Validate rectangular integer grids, dimensions, legend roles, blank separator row, wall grammar, rectangular components, legal dot counts, and override observability.

**Rationale.** The baseline validator rejected lawful authority examples yet did not establish its own advertised semantics. A validator should diagnose malformed inputs and accept the full selected authority manifold.

**Rejected alternatives.** Trust generator internals or use a permissive shape-only check.

**Probe / limit.** 60/60 defaults and 5/5 canonical inputs pass; 60/60 shared destructive mutations plus task-local malformed fixtures fail. Validation intentionally restricts the broader mathematical universe to the selected rectangular grammar.

## D10 — Retain failures and portable evidence

**Choice.** Keep the partial before battery, initial 31-test red log, intermediate failed lint/defect/semantic runs, focused tests, large census, and explicit counterexample.

**Rationale.** Later green evidence is easier to trust when the exact defects and corrections remain replayable.

**Rejected alternatives.** Delete failed iterations after achieving a green battery or rely on prose alone.

**Probe / limit.** Evidence is source-hash bound where supported. Some small red iterations were observed interactively and are summarized rather than retained as standalone logs; no success claim depends on them.
