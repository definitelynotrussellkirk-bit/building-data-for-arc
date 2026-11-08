# Native parametric family for `82bce7d23c06`

`project_only` returns the exact canonical Racket program. The alternate
`component_count_relay` first performs the complete canonical diagonal
projection, counts the same-color 8-connected objects in that produced square,
uses that count as a 1-indexed selector over source nonzero cells, and recolors
only the selected source cell's projected diagonal to color 9.

The retained wrong-intermediate program substitutes source nonzero count for
the post-projection component count. `audit.py` checks finite teaching prefixes,
matched inputs, exact 30×30 stress, named rivals, Python/Racket parity, and emits
a source-bound causal case. Native qualification and owner acceptance remain
separate gates.
