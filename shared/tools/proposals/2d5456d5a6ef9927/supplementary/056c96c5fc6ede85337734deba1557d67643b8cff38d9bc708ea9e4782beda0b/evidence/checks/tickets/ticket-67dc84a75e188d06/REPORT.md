# Allocation-quality ticket report

Ticket: `ticket-67dc84a75e188d06`  
Consumer: `bounded_owner_allocation_experiment_proposal`  
Pinned target: `83ca9df09514` / generator `70db137b815d1463c9b759c9258749291aef361633d91fbf64e7c72c8d6f2233` / rule `1dc6f00b70c9`

## Bounded comparison

The ticket seed was used for a reproducible stratified three-record sample from the 154-record normal authoring pool: the pinned target, one positive-derived-weight comparison, and one nonpositive-derived-weight comparison. The exact algorithm, candidate-pool sizes, indices, and selection-token hashes are in `selection.json`.

| Role | Record | Catalog / derived weight | Current evidence relevant to allocation |
| --- | --- | --- | --- |
| pinned target | `83ca9df09514` | `1.0 / 1.0` | Six constructive axes, six declared rivals and witnesses, no unresolved audit, no parameter workspace. |
| positive-weight comparison | `0f7d80015d9d` | `1.0 / 1.0` | Four constructive axes and a parameter workspace, but one unresolved audit is still recorded; current notes also retain a public-export identity/order follow-up. |
| nonpositive-weight comparison | `defba1ab4f90` | `1.0 / 0.0` | Five axes and two semantic rivals, but a current unresolved strict-scalar API defect is retained; repair must precede renewed data allocation. |

All three selected records are training and/or augmented sources. No ARC-GEN or RE-ARC record landed in these seeded strata, so this result does not estimate either library's quality, repair burden, or token efficiency. `inspection.json` contains current source hashes, rule hashes, source labels, axis counts, audit counts, parameter-workspace presence, and evidence availability.

## Single targeted probe

One current-source episode was built for `83ca9df09514` with four demonstrations and four independent queries using seed `7979546317262965835`, sample indices `0..7`, default difficulty, and no overrides.

- 8/8 inputs passed the generator validator and were distinct.
- 8/8 protected Racket outputs matched the Python mirror.
- The four demonstrations refuted all six declared competitors.
- `lesson_identifiable` returned `[]` for each of the four queries.
- Public challenge ID: `55335b32393b416c7497e9f913fc88090859dbc4ae308ed99b1fdf239f1e8e12`.
- The public file contains only demonstrations and query inputs; labels, seed, replay indices, and source receipts remain in `private-episode.json`.

The probe took 3.714 seconds, including 3.539 seconds reported by the protected Racket application. This is a current-source teachability/cost observation, not a model-quality measurement or a production weighting recommendation.

## Alternative bounded allocation experiment

Within this sample, current derived weights normalize to `1:1:0`; a ten-attempt owner-review pilot would therefore spend `5/5/0` attempts on the three roles. A better information-per-cost pilot is:

- **5 attempts** on current-clean, source-bound production families like `83ca9df09514`, retaining four demonstrations and four distinct Racket-labeled queries.
- **3 attempts** on positive-weight families with unresolved review or exporter concerns like `0f7d80015d9d`; no new variant/export admission until the recorded blocker is cleared.
- **2 repair/regression attempts** on nonpositive-weight families like `defba1ab4f90`; no labels are admitted until the strict-scalar defect is fixed and the exact source/rule identity is rechecked.

At eight labels per accepted episode, the hard ceiling is 80 protected labels; each family is capped at five attempts and 40 labels. This is an owner-review allocation experiment, not a mixture edit.

Stop a family immediately on source/rule drift, a Racket/Python mismatch, duplicate query input, validator failure, a named rival surviving every demonstration while changing a query, a public/private export mismatch, or any unresolved safety finding. Compare accepted distinct-query count, declared-rival rejection, Racket wall time, and repair time per accepted episode. Do not infer benefit from loss alone, and do not launch a model job under this ticket.

## Files

- `probe.py` — reproducible bounded probe and seeded selection.
- `probe.log` — actual wrapper output.
- `selection.json` — exact sample construction.
- `inspection.json` — static current-source comparison.
- `probe-result.json` — compact outcome and limits.
- `racket-receipt.json` — protected authority receipt.
- `private-episode.json` — source-bound labels/replay metadata.
- `public/55335b32393b416c7497e9f913fc88090859dbc4ae308ed99b1fdf239f1e8e12.json` — canonical public challenge bytes.
