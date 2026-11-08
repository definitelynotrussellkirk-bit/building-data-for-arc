# Native vector-translation family

`translation_mode=canonical_all` is the exact selected canonical program: the
blue-to-red anchor vector translates every non-anchor cell onto a fresh canvas.
`translation_mode=pointer_select_color` adds a genuine sequential dependency:

1. translate the unique color-8 pointer by the anchor vector;
2. use the color at that landing cell as an input-dependent intermediate;
3. translate all color-9 cargo by the same vector and paint it with that color.

Inputs are setting-neutral and count-prefix stable. The adapter accepts 2–6
demonstrations and 1–4 queries independently. Its four-query bank includes
negative directions, clipped cargo, dense distractors, and a substantive 30×30
case. Native authoring preflight executes all labels and both candidate programs
under protected Racket; owner source review and native acceptance remain separate.
