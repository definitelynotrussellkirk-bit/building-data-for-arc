# Retained counterexamples

Both cases are accepted by `self_check`, disagree with an independent rival,
and have final-source Racket outputs retained under
`checks/counterexamples-final/`.

- `component_global_right_span_case.json`: the strongest canonical-fitting
  shortcut. It extends every occupied row to the component-wide right edge,
  instead of stopping at that row's own rightmost cell.
- `per_color_row_span_case.json`: merges disconnected same-color components and
  fills through the blank space between them.

The corresponding `*_input.json` files are minimal inputs accepted directly by
`arcpuzzles apply`; the case JSONs contain exact differing cells, independent
rival outputs, source hashes, and command provenance.
