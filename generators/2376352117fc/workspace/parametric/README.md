# Parametric marker-vector direction — `2376352117fc`

Status: reviewer build; native qualification and exact-source owner acceptance are separate.

The episode-fixed parameter is `vector_direction`:

- `blue_to_red` — byte-exact canonical rule.
- `red_to_blue` — derive the same marker displacement, reverse its sign, and
  translate the green motif in the opposite direction.

Inputs are matched across settings and have stable independent prefixes for 2–6
teaching examples and 1–4 private queries. The first demonstration contains
source/target overlap; the second clips both signed translations. Together they
reject the opposite setting and the retained all-or-nothing, background-only,
preserve-input, unit-vector, same-color, and swapped-axis shortcuts.

The four queries are 12×15, 18×20, 24×27, and 30×30. The largest uses a connected
90-cell motif touching the bottom and right boundaries, so large-grid evidence is
substantive rather than padded.

The causal chain is marker extraction → input-dependent signed vector → per-cell
translation/clipping on a fresh canvas. `build_witness.py` binds the exact
qualified source and protected-Racket outputs for a wrong-vector counterfactual.
## Disjoint union candidate

All three exact disjoint programs are preserved. Opposite diagonal teaching vectors refute both component-dropping shortcuts and teach signed two-dimensional translation at the two-demo minimum. The first two scenes also reverse largest-fragment ordering and vary its size. Four independently shuffled queries mix axial and diagonal vectors, varying fragment sizes and retaining 30x30 coverage. The original and incoming samplers remain task-local; finite rival checks include unit, sign-flip and absolute-component substitutes.
