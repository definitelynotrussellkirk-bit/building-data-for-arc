# review-6d0c3d0ee8998c75 — two public-evaluation families

- `public_eval_dbff022c`: built the correspondence-table / enclosed-hole solver plus a filled-area highlighting extension.
- `public_eval_b99e7126`: built the two-scale rare-tile mask completion solver plus a completed-row highlighting extension.
- All **8/8 supplied labelled pairs** pass protected Racket: four for each public parent, including both gold-labelled test outputs.
- Fresh final focused suite: **61/61 passed**; staged copied-runtime suites are **16/16** and **45/45**, with zero failures/errors/skips.
- Both authoring preflights pass, each with four jobs; root `reference.rkt` is byte-identical to task-local `canonical.rkt`.
- Widened audits cover **1,536 episodes**, **11,776 generated pair claims**, **18,688 semantic-rival checks**, and **120 protected-Racket audit evaluations**, with zero findings.
- Public projection: **48** independently saved one-query views pass the packet checker with no privacy/structure findings.
- Protected causal replays change **41 / 35 cells** for raw-frequency / visible-pattern wrong intermediates.
- Strict single-form parser regressions cover every retained Racket source; both task trees pass Python bytecode compilation.
- Both targets are reviewer-ready prototypes; owner registration/reconciliation, unchanged native qualification, exact-source acceptance, and any training admission remain pending. `training_admitted` is false.

## `public_eval_dbff022c`

### Canonical rule

The general rule finds the unique solid 2×N or N×2 correspondence table, orients it using colors appearing outside the table, then inspects each zero-valued four-connected region. A non-edge region whose cardinal boundary is a single mapped key color is filled with the table's corresponding value; the table, frame cells, unmapped holes, and exterior background remain unchanged.

`finish_rule=fill_only` is the canonical setting. `finish_rule=highlight_dominant_fill` first performs that fill, aggregates newly filled area by mapped output color, selects the unique greatest aggregate, and recolors only those new cells with color 9. Raw frame frequency is constructively different from filled area, so the extension genuinely consumes the canonical intermediate.

The sampler supports 2–6 demonstrations and 1–4 independently presented, prefix-stable queries with matched inputs across settings and a substantive 30×30 query. Its curriculum distinguishes the correct aggregate-area rule from numeric-first, largest-single-hole, most-holes, and raw-frame-frequency shortcuts.

### Defect repaired

The strict authoring preflight exposed surplus trailing closing forms in retained Racket sources. A task-local regression now parses every source through the packet's real `strict_programs` path and requires exactly one complete rule/lambda form. The repaired canonical, alternate, counterfactual, and rival sources pass that regression and protected execution.

The retained causal witness substitutes raw frame frequency for Stage A's newly filled area totals and changes **41 final cells**.

## `public_eval_b99e7126`

### Canonical rule

The rule parses the uniform separator lattice into equal square tiles, identifies the common and rare tile patterns, and reads the color unique to the rare tile as a local mask. The visible rare copies form a subset of one translated instance of that mask on the macro tile lattice; every missing mask position is replaced with the complete rare tile while separators and all other tiles are preserved.

`finish_rule=complete_only` is canonical. `finish_rule=complete_then_highlight_densest_row` completes the macro-mask, counts completed rare tiles by macro row, selects the unique densest row, and recolors the rare tile's encoded ink cells in that row with color 9. The visible partial arrangement has a different densest row, so the second stage must consume the completed-coordinate intermediate.

The sampler supports 2–6 demonstrations, 1–4 independent queries, matched setting-neutral inputs, independently shuffled presentation, and a substantive 30×30 case using a 29×29 seven-tile lattice plus a final separator band.

### Defects repaired

Strict parsing first found surplus trailing forms in the alternate and counterfactual Racket sources; the same one-complete-form regression now covers this task.

The widened sampler audit then found a real minimum-lesson ambiguity at seeds **11** and **16**: reflecting the encoded 3×3 macro-mask fit both visible demonstrations but changed a later query. The exact counterexamples were converted into a failing regression. Demonstration 1 now always uses an asymmetric encoded mask, and the regression passes for seeds 0–31; the final audit extends through seeds 0–127 with no harmful survivor.

The protected wrong-intermediate witness ranks only the visible partial macro arrangement instead of the completed mask and changes **35 final cells**.

## Evidence map

For each task, `checks/TASK/preflight/{preflight,execution,original-pairs}.json` is the authoritative authoring receipt. `checks/TASK/adversarial/report.json` and `private/index.json` bind the widened finite-rival and public/private checks. `checks/TASK/public-check/result.json` validates all saved one-query files. `checks/TASK/causal/{witness,replay,summary}.json` contains the source-bound protected counterfactual. `checks/TASK/task-tests/` contains the copied-runtime test receipt and JUnit report. Combined source identity, fresh pytest, compile, and aggregate verification are under `checks/combined/`.

The rival banks and seed sweeps are bounded reviewer evidence, not proofs against arbitrary programs or guarantees of learning benefit. These are authoring preflights, not owner qualification or acceptance. The owner must preserve/reconcile exact source, register each parent, refresh its native inventory, run unchanged native qualification and fresh acceptance, and separately decide any training admission.
