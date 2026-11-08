# Working notes: f16508733f0a

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review 2026-10-02: colour agreement and simultaneity

Version 2.1.0 adds an authority-ignored mixed-colour decoy in multicolour connected scenes, without changing the Racket rule or exact override ranges. A 2×5 main bar plus an existing-palette accent preserves both the colour-agreement and single-pass counterexamples. The accent is included in placement support/halo reservations. Single-colour connected scenes keep the earlier motif.

Five new tests failed on the baseline; all fourteen task tests pass after the repair. The final generator hash is `014738f8da97eb5f6d38e6e631b7bf5a3584f16bfce10c4a82cbd7b428265c2b`. A 648-draw, 360-unique-input Racket census (seeds 0–23, indices 0–8, all bands) had zero mirror mismatches. All 432 overlapping three-demo windows refuted the five live rivals. Before/after batteries each had twelve green stages. These are sampled checks, not model-training measurements.

Preserve the mixed-colour near-match and a later-pass-only zero together in any future shape rewrite. The earlier rationale excluding mixed-colour windows was deliberately rejected: labelled near-matches disambiguate the equality predicate. Mixed-only/no-target scenes, conflicting colours claiming one hole and unused palette colours remain rejected. See the retained return's REVIEW.md and DECISIONS.md for evidence and limitations; workspace tools reproduce the measurements.
## Current reviewer considerations

Source SHA-256: `014738f8da97eb5f6d38e6e631b7bf5a3584f16bfce10c4a82cbd7b428265c2b`.

# Distribution and implementation decisions

## D1 — Keep the authoritative task
The selected Racket rule scans original-input 2×2 windows, requiring exactly three equal nonzero entries and one zero. It writes into a separate output. This remains the authority, not a Python-generated replacement. Background stays zero; fixed colour roles were not invented. All four normalized canonical input/output pairs remain accepted and all five declared rivals fit those pairs. Evidence: the before/after authority-sync reports and `checks/focused-final/report.json`.

## D2 — Add informative negatives, not random noise (G1)
The old source explicitly excluded mixed-colour three-of-four windows because it considered their appearance ambiguous. That rationale is visible in the frozen source; it is not guessed from intent. But the rule is unambiguous: these windows must be ignored. Their exclusion made a majority-colour rival indistinguishable on 108/108 baseline draws. The new validator allows them alongside real completion targets while preserving malformed-grid checks, conflict checks, required positive targets and the requirement that every foreground colour participates in a real target. A mixed-only grid remains invalid under this positive-lesson grammar.

This broadens the documented input grammar deliberately; it does not alter labels or weaken an authority parity check. The old impostor regression still passes, and the new regression explicitly accepts an informative mixed-colour decoy.

## D3 — Retain simultaneity while adding colour contrast (G2)
The original connected module is a 2×4 five-cell bar. It already refutes component completion and iterative closure. For multicolour connected scenes, the new module uses a 2×5 six-cell main shape and a differently coloured endpoint. Two legitimate local holes fill; another zero remains unchanged beside a mixed-colour near-match and only becomes fillable on a later pass. Eight rotations/reflections randomize orientation. Pure single-colour connected scenes retain the earlier module.

A compact accent placed in the old 2×4 module was considered but not implemented: filling its only remaining endpoint would destroy that module's closure counterexample. Arbitrary disconnected distractor placement was also considered but not implemented: it would consume more packing space and introduce avoidable small-grid incompatibilities. These are design comparisons, not fabricated experimental runs.

## D4 — Reserve coloured support, not just the main object
The accent participates in placement occupancy/halo constraints. Its absolute coordinate is recovered from the translated normalized support; all other cells get the main colour. This prevents a new accent from accidentally touching a separately placed motif. It reuses an existing target colour different from the main colour, so `color_count` keeps its exact existing interpretation. A connected scene has at least three modules, supporting the maximum three-colour request without a colour that appears only decoratively.

## D5 — Preserve exact axes and the curriculum length
No new override axis was necessary. `grid_h`, `grid_w`, `target_count`, `color_count`, `layout_mode` and `corner_diversity` retain their types and full ranges. Exhaustive categorical/count combinations at the smallest grid and the existing endpoint matrix all pass. The six-slot curriculum is retained: multicolour connected slots 0 and 3 supply the new colour-agreement witness, so every three consecutive default slots contain one. Connected slots supply the closure witness; repeated-colour controls remain present. `EXAMPLES_NEEDED` remains 3.

This guarantee applies to the **default sequential sampling policy**. Overrides can request only isolated or one-colour scenes; those requests remain lawful, but their assembled lessons must still go through `lesson_identifiable` when a query requires an unseen distinction. Shuffling unrelated rows or sampling with replacement is not covered by the cyclic-window guarantee.

## D6 — Make claims executable
Two additional pure rival solvers and claim-bearing witnesses are registered alongside the existing three. The portable census reads the live registries rather than a copied rival-name list, checks every usable canonical pair, and evaluates every cyclic lesson start. Its baseline-only diagnostic competitors are labelled as diagnostics. All failures, first counterexamples and actual runtime directories are retained.

The new tests were written before the generator change. Five failed on the baseline; after the repair all 14 task-local tests pass. The original seven tests are unchanged. A comment was corrected afterward to distinguish 54 combinations from 216 seeded draws; it did not alter generator bytes or invalidate the solve.

## D7 — Keep measurement denominators honest
Canonical-size slots intentionally do not vary with difficulty. Thus the final 648 sampled draws contain only 360 unique grids, and 432 lesson windows overlap. These are not claimed as independent samples. Baseline and intermediate counts use seeds 0–3; final counts use seeds 0–23. Every report carries the corresponding full generator hash; the final implementation is the one bound to the fresh solve.

## D8 — Scope and remaining limits
The two audit targets are untouched. Shared runtime and test fixes are suggestions, not unsolicited source edits. No helper imports a predecessor checkout. The packet does not contain Git metadata; source review used its immutable baseline and manifest instead of initializing a replacement history.

The constructive grammar still has only one large connected module family per colour-count branch, separated modules, 4–6 target windows, at most three foreground colours and no all-no-op lessons. These restrictions keep bounded exact-axis generation reliable but do not represent every lawful grid of the Racket function. Finite rival coverage cannot prove full identifiability or a Qwen training benefit. Future experiments should measure held-out structural generalization and avoid random row-level train/test splitting of this related family.

## Friction and alleviation
The general repository test command does not collect newly added task-local tests, and frozen runtime mappings do not automatically know new filenames. The new portable runner copies the actual task test directory, making the intended verification explicit. Check output directories must be new: console logs now live outside them until the check finishes. The unrelated 0.2-second startup fixture failure is retained with a diagnostic that separates Python site startup from stream capture instead of masking it or changing shared code.
