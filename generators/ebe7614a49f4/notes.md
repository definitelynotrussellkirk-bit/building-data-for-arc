# Review notes: ebe7614a49f4

## Current decision

Keep the selected canonical rule unchanged: blue (`1`) activates rows, red
(`2`) activates columns, and the output is a fresh grid containing green (`3`)
at every active-row × active-column intersection. The canonical program remains
byte-exact at SHA-256
`0f1e6548baedcd0ea8b6452e7694e08bca40bd17572db63787d081cc0194faef`.

## Base-generator repair

The v2 generator advertised ten controls, but several were aliases, constants,
or deliberately invalid degenerates; it also stopped at 12×12 and used
coercive/non-strict control handling. Version 3.0.0 replaces that surface with
six observable controls: `grid_h`, `grid_w`, `n_active_rows`, `n_active_cols`,
`marker_redundancy`, and `layout`. It supports 6×6 through 30×30, rejects
unknown/coercive inputs, is deterministic through `GenCtx`, supplies a Python
rule mirror, and keeps all marker cells distinct.

Two defects found by the final control matrix were repaired rather than waived:

1. Explicit legal axis endpoints were being constrained by the selected
   difficulty band. Overrides now use the full declared axis range while
   unforced sampling remains difficulty-aware.
2. Dense 6×6 `crossed_markers` scenes could fill an active column with blue
   markers before red placement. The constructor now reserves the required red
   capacity in every active column.

The retained audit covers 896 ordinary draws, 384 explicit 6×6/30×30 corner
combinations, and five strict rejection cases with zero final failures.

## Native parametric family

The episode-fixed parameter is `render`:

- `points` is the exact canonical program and default setting.
- `rays` first computes the canonical intersection coordinates. Only direction
  codes (`4` up, `5` right, `6` down, `7` left) at those selected coordinates
  launch rays; each ray stops at color `8` or the grid boundary, and the union is
  painted green. Direction codes elsewhere are explicit decoys.

Inputs are setting-independent, every episode supports 2–6 demonstrations and
exactly four distinct private queries, and the fixed size schedule reaches
30×30. The two-demo lesson refutes eight authored shortcut families. Crossed
controls separately perturb decoy codes and selected codes to show that the
intersection intermediate—not generic token presence—controls the output.

## Causal dependency

Step A finds active rows and active columns and forms their Cartesian-product
coordinates. The intermediate is the ordered set of those input-dependent
coordinates. Step B reads and traces only the direction codes at those
coordinates. The protected-Racket `skip_a` witness launches from all direction
tokens instead: the retained case has 9 selected starts, 40 intended green
cells, and 59 counterfactual green cells.

## Final evidence and limits

- Focused changed-target suite: 16 passed.
- Bounded adversarial sweep: 128 seeds, 512 episodes, 2,048 matched input pairs,
  eight shortcut families, strict tamper rejection, privacy checks, and a
  substantive 30×30 case with 239 routed cells.
- Authoring preflight: four jobs across both settings, 24 parametric labels,
  three canonical pairs, and 32 protected-Racket evaluations.
- Sequential export: 16 one-query public views; 24 first-turn invariance checks
  and four positive controls passed.

This is reviewer-ready source, not owner acceptance or training admission. The
owner must integrate the exact patch, repeat native source review,
qualification, witness replay, and acceptance. The causal and shortcut evidence
is finite and authored; it is not a universal uniqueness or depth proof.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
