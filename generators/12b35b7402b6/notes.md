# Review notes: 12b35b7402b6

## Repaired base contract

- Removed diagnostic `texture` values that could create two matching blue
  objects or no canonical match while still passing the old self-check.
- Rejects unknown controls, booleans, wrong types, and out-of-range values.
- Honors exact grid, marker-count, object-count, and marker-layout overrides.
- Separates marker count from horizontal span through scattered layouts, so a
  span-based program is no longer accidentally taught.

## Parametric design

- `canonical`: exact selected authority bytes.
- `linked_payload`: canonical recoloring creates a red bridge between at least
  two originally separate red components. Stage B recomputes the intermediate's
  red components and uses the unique largest component size to select an azure
  payload. The protected `skip_stage_a.rkt` counterfactual selects a different
  payload.
- Inputs are setting-neutral. Two-demo teaching examples cross marker span,
  target position/rank, pre-stage red size, skip-stage delta, 4-vs-8-connectivity
  delta, payload rank, and marker-relative distance.
- The fourth query is a substantive 30x30 stress case.

## Adversarial findings retained

The first sampler admitted fixed `+1` size, 8-connectivity `+1`, single-anchor
arithmetic, target-bounding-box, and marker-distance shortcuts. Each was
reproduced, repaired in the grammar, added to the rival bank, and pinned by
focused tests. The reusable semantic and protected-Racket probes remain under
`workspace/parametric/` for later agents.

## Limits

Reviewer evidence is finite and source-bound. It does not grant owner source
approval, native acceptance, official-query gold verification, training
admission, or training activation.
