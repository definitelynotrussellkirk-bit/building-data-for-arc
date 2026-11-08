# Parametric local vote plus output-mode finish

`finish_rule=vote_only` is the byte-exact canonical three-panel voting rule.
`finish_rule=vote_then_keep_output_mode` first materializes that full voted grid,
then computes its unique nonzero modal color and erases all other voted colors.
The sampler deliberately makes the raw-panel global mode a different color, so
Stage B cannot be replaced by a pre-vote frequency shortcut.

Inputs are setting-independent and support 2–6 demonstrations plus 1–4
prefix-stable queries. The largest lawful rectangular stress is 30×29: with
three equal panels and two one-column separators, total width is `3*pw+2`, so
exactly 30 columns is impossible. The fourth query fills a substantive 30×29
canvas and touches every boundary with foreground content.
