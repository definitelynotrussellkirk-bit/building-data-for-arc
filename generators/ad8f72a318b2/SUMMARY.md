# ad8f72a318b2

Fixed 11×9 control-strip + four-panel library task. Row 0 columns 0–3 are a left-aligned unary selector (the count of blue `1` cells chooses panel 1–4); column 5 is a transform code (`1` identity, `2` clockwise, `3` 180°, `4` counter-clockwise, `5` left-right reflection); column 7 is the output color. Four monochrome connected 4×4 panel shapes begin at `(2,0)`, `(2,5)`, `(7,0)`, and `(7,5)`. Select the requested panel, crop its nonzero support, transform it, and recolor every foreground cell to the target color.

Generated panels are pairwise distinct up to dihedral symmetry and individually distinguish all five advertised transforms. The 60-profile curriculum uses five demonstrations and one query; every production five-demo window covers all four selectors, all five transform codes, and target colors that are absent from, equal to the selected panel, or equal to an unselected panel. Declared semantic rivals are refuted under every cyclic start and every choice of query position tested by the task-local suite.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical Racket authority is unchanged and pinned by `RULE_HASH = "5d4b4a902077"`.
