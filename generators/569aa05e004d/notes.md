# Working notes: 569aa05e004d

## Current decision

Keep the production generator and canonical rule unchanged. The canonical source
was checked through 800 bounded draws spanning every declared `difficulty`,
`layout`, `texture`, `edge_profile`, and `color_reuse` combination; its mirror was
nontrivial and its self-check/override observations agreed on every draw.

The native family parameter is `closure_axis`:

- `rows_only` is the exact selected canonical Racket program. Starting from zero,
  it fills an inclusive horizontal interval only when a color occurs exactly twice
  in that input row.
- `rows_then_columns` runs that exact row pass, then counts colors in each column of
  the input-dependent Stage-A grid. Exact pairs fill only background cells between
  their two rows, preserving all Stage-A foreground.

Inputs are deterministic, distinct, and identical across settings. The family
supports 2–6 demonstrations and exactly four private queries. The minimum two-demo
lesson contains multi-pair rows, erased singleton/triple/blocker controls, exact
three-occurrence column controls, and a raw-input vertical decoy whose relation is
changed by Stage A. Query profiles include wide, tall, boundary-touching, dense,
and substantive 30×30 cases.

## Adversarial repair

A fresh source review found that the first Stage-B implementation could overwrite
a differently colored horizontal Stage-A bar at a row/column intersection. That
violated the documented preservation rule even though ordinary generated scenes
avoided competing writes. The rule was repaired in both Python and Racket so the
column pass writes only into zero cells. The smallest retained regression uses the
intermediate `[[2], [3], [0], [2]]`, whose correct result is
`[[2], [3], [2], [2]]`. The reusable audit now checks the preservation invariant on
every generated pair, preventing scene pruning from masking a recurrence.

The final bounded attack bank covers fixed color/rank/location rules, raw-input and
partial-intermediate substitutes, exact-two versus at-least-two counts, setting and
demo-count independence, crossed causal/nuisance controls, malformed/forged
certificates, protected-Racket parity, boundaries, and 30×30 stress. Final evidence:
320 episodes / 2,560 pairs in the all-demo-count Python run, 64 episodes / 512 pairs
and 48 protected-Racket evaluations in the Racket run, six certificate forgeries
rejected, and no declared shortcut survivor.

## Causal evidence and limits

The protected counterfactual skips Stage A and runs the column rule on the raw
input. It changes 81 cells on the retained 9×21 case and 311 cells on the retained
30×30 case. Stage B adds 24 and 160 cells respectively while preserving every
nonzero Stage-A cell.

The artifact is ready for exact-source owner review and native admission. The
qualification and witness are reviewer authoring evidence, not owner acceptance or
training admission. Finite generated attacks do not prove universal uniqueness; a
future owner should rerun qualification and acceptance on the integrated bytes.
