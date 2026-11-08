# Current notes: b1e6ee6856bf

## Intended rule

On a zero-background grid, process each column independently. Preserve only the topmost nonzero cell with its original color and erase every lower nonzero cell. Empty columns remain empty. Canonical/Racket rule hash: `3a3d82df16cd`; Racket remains the authority.

## Current generator

Version `2.0.0`; SHA-256 `50a43c7c02bdd7a277ef01aea7220e974e73d6b02644ce8333851fd0c574fd20`.

Public exact axes:

- `grid_h`: 5…14
- `grid_w`: 5…14
- `n_cols`: 1…5
- `stack_depth`: 2…5

Every joint combination is constructive in every difficulty band. Unknown axes and non-integer override values fail loudly. Difficulty affects default weighting only, not exact feasibility.

Default production draws are deterministic, nonidentity, and contain a column of depth at least three. Exact depth two is retained for canonical-like/boundary probes. A period-four schedule emits one 5×5/all-colors canonical-profile sample and three broad samples; exact overrides take precedence.

`self_check` accepts all four canonical inputs and the reviewed scattered-column domain. It excludes full-foreground textures and a lone solid 2×2 foreground block, the two minimal impostor families reproduced by strict defect lint.

## Semantic contract

Declared witnesses:

- `nonidentity_column` refutes identity and keep-bottommost.
- `three_cell_column` refutes `erase_one_bottom_cell`.

The last rival agrees with every usable canonical pair because canonical columns have depth at most two. Retained counterexample: `counterexamples/erase_one_bottom_cell.json`.

Lessons use three demonstrations and one query. Final source-bound census: 100 lessons per easy/medium/hard, 300/300 materialized, 1,200 unique pairs, and all 1,200 hold-one-pair-out rotations; zero ambiguities, hook warnings, or scoring errors against the declarations. This is finite evidence only.

## Decision reversal and evidence

The prior v1.3.0 design advertised nine axes and special degenerate textures. The source-bound prior audit in `evidence/review_index.json` was used as a lead for baseline SHA-256 `90893c976a71825e5432c988a6e01374a7f0c631c6a93864634cf705cf70f5ff`. The required before battery independently reproduced lint, defect-lint, and override failures, including ignored exact dimensions, accepted unknown keys, dead axes, generation errors, and self-rejected identity outputs.

That design was replaced rather than patched branch-by-branch because only four controls represented stable, observable task variation. Final evidence:

- battery: 12/12 green;
- focused tests: 40/40 passed;
- override: 29,880/29,880 accepted, zero findings, unknown key rejected;
- profile floor: 15/60 exact, every band supported;
- semantic gate: strict 600/600, witnesses 2/2, 12/12 lessons, 0/48 diagnostic rotation ambiguity;
- large census: 300 production lessons and 1,200 required rotations, zero declared-rival ambiguity.

## Known limits and open status

- Reviewed support is sparse column scatters on 5…14 grids, at most five occupied columns, and maximum depth five; arbitrary dense textures are out of scope.
- The fixed schedule is observable from sample index, although generation indices are not intended as training features.
- Declared-rival success is not a proof of unique induction against all programs.
- No Racket/canonical bytes changed.
- Catalog approval and training admission remain unchanged/false pending maintainer intake.
## Current reviewer considerations

Source SHA-256: `50a43c7c02bdd7a277ef01aea7220e974e73d6b02644ce8333851fd0c574fd20`.

# Decisions: b1e6ee6856bf

All decisions below are bound to final generator SHA-256 `50a43c7c02bdd7a277ef01aea7220e974e73d6b02644ce8333851fd0c574fd20`. IDs match `REVIEW.md` where applicable.

## D1 / R1 — Replace the nine-axis façade with four observable exact controls

**Prior choice.** v1.3.0 advertised `grid_h`, `grid_w`, `palette_kind`, `n_cols`, `density`, `palette_size`, `position_bias`, `n_distinct_colors`, and `texture`. The comments suggest combinatorial variety was the rationale, but no stronger source-bound rationale was recorded. Degenerate `texture` branches bypassed `gen_ctx`; several controls were aliases, constants, ignored, or only feasible in some bands.

**New choice.** Expose only `grid_h`, `grid_w`, `n_cols`, and `stack_depth`, with compact integer domains that are constructive in every band and recoverable by `observe_overrides`.

**Why.** The baseline override stage produced 20,492 categorized findings over 119,700 draws and accepted the unknown-key probe. A public control should either be exact and observable or not be public.

**Alternatives rejected.** Keeping the old axes and adding special cases would preserve misleading semantics and a much larger cross-product. Declaring many incompatibilities would technically quiet checks while leaving a poor authoring API. Hidden non-exact “style” inputs were unnecessary for this one-operation rule.

**Probe.** Final override matrix: 332 cases × 3 bands × 30 seeds = 29,880 draws, all accepted, zero findings/warnings; unknown key rejected. Evidence: `checks/after-final-bg/checks/b1e6ee6856bf_after_override_results.json`.

**Failure modes/limits.** The reviewed domain is intentionally 5…14 rows/columns, 1…5 occupied columns, and maximum depth 2…5. It does not claim support outside those bounds.

## D2 / R1 — Keep exact domains identical across difficulty bands

**Prior choice.** Difficulty branches changed the draw bounds themselves, so otherwise documented exact values failed in some bands.

**New choice.** Difficulty changes only the default weighting, never the legal domain used when an exact override is supplied.

**Why.** This makes the API compositional and testable: the same requested grid has the same meaning in easy, medium, hard, or default mode.

**Alternatives rejected.** Band-specific advertised domains would be honest but more complex and would reduce useful cross-band comparisons. Silent clipping, used by the baseline for `n_cols`, was rejected because it destroys exactness.

**Probe.** Focused tests request the upper boundary `(14,14,5,5)` in every band and compare `observe_overrides` exactly.

**Failure modes/limits.** Default distributions still differ by band; only exact feasibility is invariant.

## D3 — Schedule canonical shape/palette support explicitly

**Prior choice.** Random sampling did not reach any canonical profile in the 60-draw floor check.

**New choice.** Use a deterministic period-four schedule: one 5×5/all-colors `canonical_palette` sample, then three broad samples. Exact overrides disable the scheduled special case so caller intent remains authoritative.

**Why.** Canonical-support coverage should not depend on a low-probability coincidence. A fixed schedule is cheap, replayable, and gives every band support while leaving 75% of default draws broad.

**Alternatives rejected.** Pure random mixture could miss the floor and make regression tests flaky. Making every draw canonical-like would collapse geometry. A band-specific schedule was unnecessary.

**Probe.** Final profile floor: 15/60 exact hits, with easy 4/20, medium 5/20, hard 6/20. Semantic schedule census observed both profiles in every band.

**Failure modes/limits.** Sample indices are not intended as model inputs. A system exposing them could learn the periodic profile selector, although both profiles carry the same transformation rule.

## D4 / R2 — Force a three-cell witness in default lessons

**Prior choice.** The canonical examples and baseline sampling established nonidentity, but did not explicitly protect against the shortcut “erase only one lower cell per occupied column.” All four usable canonical pairs have maximum column depth two, so that rival fits all of them.

**New choice.** Default `stack_depth` begins at three, and the first selected column always realizes it. Exact depth two remains legal for boundary and canonical-like probes.

**Why.** A depth-three column changes the rival’s prediction: the rival leaves the middle cell, while the true rule erases it. This is a task-semantic witness rather than generic diversity.

**Alternatives rejected.** More demonstrations without controlling their depth do not guarantee refutation. Removing depth-two support entirely would unnecessarily narrow the lawful domain. Changing the Racket rule would be incorrect.

**Probe.** `counterexamples/erase_one_bottom_cell.json`; semantic gate’s `three_cell_column` witness fired 600/600 and its rival claim held 60/60; final census refuted the rival in 300/300 lessons and all 1,200 rotations.

**Failure modes/limits.** This addresses three declared plausible rivals, not the entire hypothesis space.

## D5 — Use three demonstrations, then require all hold-one-pair-out rotations to be identifiable

**Prior choice.** v1.3.0 declared four examples but had no executable lesson-identifiability contract.

**New choice.** Set `EXAMPLES_NEEDED=3`, declare rivals/witnesses, and require the larger census to hold out each of the four labeled pairs once.

**Why.** Every generated pair carries the depth-three witness, so three demonstrations are sufficient against the declared competitors. Rotation testing prevents a favorable fixed query position from hiding a teaching defect.

**Alternatives rejected.** Keeping four demonstrations adds cost without improving the tested distinction. Treating the small 12-lesson semantic smoke test as sufficient was rejected because the canonical-fitting rival justified the required 100-per-band census.

**Probe.** 300 production lessons and 1,200 required rotations, zero declared-rival ambiguity/warnings/errors; 1,200 unique inputs. Evidence: `checks/lesson-census-final.json`.

**Failure modes/limits.** Rotations reuse materialized bundles and do not enumerate all fresh cyclic lesson windows or undeclared rivals.

## D6 / R3 — Narrow only the dense impostors demonstrated by defect lint

**Prior choice.** `self_check` accepted any rectangular color grid with a multi-cell column, including a full one-color texture and a lone solid 2×2 block.

**New choice.** Require visible zero background and reject only the lone solid 2×2 foreground block, while preserving the broader scattered-column grammar and all canonical inputs.

**Why.** The strict defect linter supplied concrete accepted impostor families. The minimal restriction resolves those without converting `self_check` into a copy of the sampler.

**Alternatives rejected.** Requiring every input to match one exact generation recipe would reject lawful canonical/support cases. Ignoring the warning would leave a validator whose accepted domain includes visually unrelated texture tasks.

**Probe.** The regression was written first and failed; after the change, 40/40 task tests and final defect lint pass. Boundary generation tests scan 128 seeds for dense-prone override combinations and verify exact axes remain intact.

**Failure modes/limits.** Other unusual lawful grids may remain validator-only. The validator intentionally checks the reviewed task grammar, not probability under the sampler.

## D7 — Do not modify Racket authority

**Prior choice.** The selected canonical rule already implemented the intended transformation and passed canonical/rule-smoke checks.

**New choice.** Repair only generation, validation, metadata, and tests.

**Why.** All reproduced defects were in the input/lesson contract. Changing the rule would introduce risk without addressing them.

**Alternatives rejected.** None justified by evidence.

**Probe.** Canonical file SHA-256 is unchanged at `f5aa554e2aa0959cddca2a4a693e3524f8ad2836fbdff7f85a481058bcded6ee`; authority/rule-smoke/racket-lint stages are green.

## D8 — Preserve audit findings without patching unrelated targets

The drawn audit targets `1409f5f7af2e` and `677dcb71e2be` have source-bound curriculum shortcuts. Per assignment, I retained exact probes and Racket counterexamples under `checks/audit/` but did not alter those generators. See `AUDIT.md`.

## Native parametric family: skyline color selection

The separate `workspace/parametric/` family preserves production2.0.0 and exact
canonical Racket bytes. `survivor_filter=all` is canonical; `modal_color` extracts
the same topmost-column skyline, counts its colors and retains every tied mode.
The second selection depends on the first: raw-grid color counts and skipped
column extraction change qualified outputs in two protected causal cases.
This is an input-dependent composition of selections, not iterative simulation.

The native grammar is exact-list rectangular1..30 integer0..9 grids with explicit
background0, including dense, empty and one-cell cases. Production remains its
reviewed5..14 sparse-column grammar. The API accepts3..6demos and1..4queries.
Complete banks precede prefixes; local SHA-derived layout/palette/query streams
keep inputs matched across settings and leave global RNG untouched. Three demos
teach a below-half plurality, tied winners with minorities, and singleton ties.

Observed repair: initial30x30 stress at seeds0,17,max had all skyline colors tied,
so both settings coincided. Three failing regressions preserve that finding.
The repaired30x30 role recolors one top only when all colors tie, after constructing
the original geometry. It preserves other query roles and demos. Current max-seed
input has615foreground cells spanning30x30 and touching all edges; outputs retain
30canonical or11modal cells. Output sparsity is inherent to column-top selection.

Current bounded results:99focused tests;54core rival comparisons all demo-refuted;
20independent comparisons with14demo refutations and6finite-consistent canonical
cases, no query conflicts/errors;20max-count/max-seed protected labels;4native
qualification jobs and40protected evaluations;2causal counterfactuals replayed;
16single-query public views with four corruptions rejected. All six consistent
independent comparisons disable color ranking under canonical-all and agree on
the tested queries. Finite evidence does not prove universal uniqueness.

Evidence inventory: `workspace/parametric/evidence/manifest.json`. Return evidence
is under `checks/b1e6ee6856bf/`, with current `audit-repaired/audit.json`,
`independent-rivals-after-stress.json`, `qualification/`, `causal/`, and
`public-probe.json`; pre-repair/RED records are historical. The inherited audit
targets an older production hash and is not resolved by this native extension.
Next owner action: qualify and freshly accept these exact integrated native
sources. Reviewer readiness grants no training admission or mixture change.
